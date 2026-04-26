"""
Management command to rebuild all FAISS indexes with the improved embedding engine.

Usage:
    python manage.py rebuild_indexes

This is required after upgrading the embedding engine because:
    - The old indexes used bag-of-words hashing (L2 distance)
    - The new indexes use BM25 TF-IDF embeddings (Inner Product / cosine similarity)
    - Old index files are incompatible and must be rebuilt

The command will:
    1. Delete all existing FAISS index files
    2. Re-process all documents in the database
    3. Re-embed and re-index all chunks
"""

import os
import shutil
import logging

from django.core.management.base import BaseCommand
from django.conf import settings

from documents.models import Document
from documents.services import extract_text_from_pdf, chunk_text
from ai.vector import get_vector_store, reset_vector_store, DEPARTMENTS
from ai.embeddings import get_embedding_engine
from ai.cache import get_search_cache

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Rebuild all FAISS indexes with the improved embedding engine'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.WARNING('\n=== FAISS Index Rebuild ===\n'))

        # Step 1: Show current state
        documents = Document.objects.filter(is_processed=True)
        self.stdout.write(f'Found {documents.count()} processed documents to re-index')

        if dry_run:
            for doc in documents:
                self.stdout.write(f'  - [{doc.department.upper()}] {doc.filename} ({doc.chunk_count} chunks)')
            self.stdout.write(self.style.WARNING('\nDry run — no changes made.'))
            return

        # Step 2: Delete old index files
        index_dir = settings.FAISS_INDEX_DIR
        self.stdout.write(f'\nClearing old indexes in: {index_dir}')

        for dept in DEPARTMENTS:
            for ext in ['_index.faiss', '_metadata.json']:
                path = os.path.join(index_dir, f'{dept}{ext}')
                if os.path.exists(path):
                    os.remove(path)
                    self.stdout.write(f'  Deleted: {dept}{ext}')

        # Also remove old vocabulary and IDF stats
        for fname in ['vocabulary.json', 'idf_stats.json']:
            path = os.path.join(index_dir, fname)
            if os.path.exists(path):
                os.remove(path)
                self.stdout.write(f'  Deleted: {fname}')

        # Step 3: Reset singletons
        reset_vector_store()
        get_search_cache().invalidate()

        # Step 4: Re-process each document
        self.stdout.write('\nRe-indexing documents...\n')

        total_chunks = 0
        errors = 0

        for doc in documents:
            try:
                # Extract text
                doc.file.open('rb')
                text = extract_text_from_pdf(doc.file)
                chunks = chunk_text(text)

                if not chunks:
                    self.stdout.write(
                        self.style.WARNING(f'  [{doc.department.upper()}] {doc.filename}: no chunks extracted')
                    )
                    continue

                # Add to new index
                vector_store = get_vector_store()
                added = vector_store.add_chunks(doc.department, chunks, document_id=doc.id)

                # Update document record
                doc.chunk_count = added
                doc.save(update_fields=['chunk_count'])

                total_chunks += added
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  [{doc.department.upper()}] {doc.filename}: {added} chunks indexed'
                    )
                )

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'  [{doc.department.upper()}] {doc.filename}: ERROR - {str(e)}')
                )
            finally:
                try:
                    doc.file.close()
                except Exception:
                    pass

        # Step 5: Summary
        self.stdout.write(f'\n=== Rebuild Complete ===')
        self.stdout.write(f'Documents processed: {documents.count() - errors}')
        self.stdout.write(f'Total chunks indexed: {total_chunks}')
        if errors:
            self.stdout.write(self.style.ERROR(f'Errors: {errors}'))

        # Show new index stats
        vector_store = get_vector_store()
        stats = vector_store.get_index_stats()
        self.stdout.write(f'\nNew index stats:')
        for dept, info in stats.items():
            self.stdout.write(f'  {dept.upper()}: {info["total_vectors"]} vectors')

        self.stdout.write(self.style.SUCCESS('\nDone!'))
