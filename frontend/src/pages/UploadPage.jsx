import { useEffect, useState } from 'react';
import AppLayout from '../components/AppLayout';
import { useAuth } from '../context/AuthContext';
import { uploadDocument, listDocuments } from '../services/uploadService';
import { ROLE } from '../utils/roles';
import { logError, logInfo } from '../utils/logger';
import { trackEvent } from '../firebase';

export default function UploadPage() {
  const { backendUser } = useAuth();
  const departments = backendUser?.departments || [];
  const defaultDept = departments[0] || '';

  const [file, setFile] = useState(null);
  const [department, setDepartment] = useState(defaultDept);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [documents, setDocuments] = useState([]);
  const [fetching, setFetching] = useState(false);

  const isAdmin = backendUser?.role === ROLE.ADMINISTRATOR;

  useEffect(() => {
    if (!department && defaultDept) {
      setDepartment(defaultDept);
    }
    fetchDocuments();
  }, [department, defaultDept]);

  const fetchDocuments = async () => {
    setFetching(true);
    try {
      const data = await listDocuments();
      setDocuments(data);
    } catch (err) {
      logError('Failed to fetch documents:', err);
    } finally {
      setFetching(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    if (!file) {
      setError('Please choose a PDF file first.');
      setLoading(false);
      return;
    }

    try {
      const uploadDept = isAdmin ? department : defaultDept;
      const payload = { file, department: uploadDept };
      const response = await uploadDocument(payload);
      logInfo('Upload success:', response);
      trackEvent('document_upload', { department: uploadDept, file_size: file.size });
      setMessage('Document uploaded successfully.');
      setFile(null);
      fetchDocuments(); // Refresh list
    } catch (err) {
      logError('Upload failed:', err);
      const apiMessage = err?.response?.data?.error || err?.response?.data?.detail;
      setError(apiMessage || 'Upload failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="card max-w-2xl">
          <h1 className="text-base font-semibold">Upload document</h1>
          <p className="mt-2 text-sm text-gray-500">Only authorized department uploads are allowed.</p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium">Department</label>
              {isAdmin ? (
                <select className="input" value={department} onChange={(e) => setDepartment(e.target.value)}>
                  {departments.map((dept) => (
                    <option key={dept} value={dept}>{dept.toUpperCase()}</option>
                  ))}
                </select>
              ) : (
                <input className="input capitalize" value={defaultDept} readOnly />
              )}
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">PDF File</label>
              <input
                className="input file:mr-3 file:rounded-lg file:border-0 file:bg-soft file:px-3 file:py-2 file:text-sm"
                type="file"
                accept="application/pdf"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </div>

            {message ? <p className="rounded-xl bg-soft px-3 py-2 text-sm text-gray-700">{message}</p> : null}
            {error ? <p className="rounded-xl bg-soft px-3 py-2 text-sm text-gray-700">{error}</p> : null}

            <button className="btn-primary" type="submit" disabled={loading}>
              {loading ? 'Uploading...' : 'Upload'}
            </button>
          </form>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold">Uploaded Documents</h2>
            <button 
              onClick={fetchDocuments} 
              className="text-xs text-primary hover:underline"
              disabled={fetching}
            >
              {fetching ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
          <p className="mt-1 text-sm text-gray-500">List of documents you have access to.</p>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-border text-gray-500">
                  <th className="pb-2 font-medium">Filename</th>
                  <th className="pb-2 font-medium">Department</th>
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium text-right">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {documents.length === 0 && !fetching ? (
                  <tr>
                    <td colSpan="4" className="py-4 text-center text-gray-400 italic">No documents found.</td>
                  </tr>
                ) : (
                  documents.map((doc) => (
                    <tr key={doc.id}>
                      <td className="py-3 font-medium text-gray-900">{doc.filename}</td>
                      <td className="py-3 uppercase text-gray-500">{doc.department}</td>
                      <td className="py-3">
                        {doc.is_processed ? (
                          <span className="rounded-full bg-green-50 px-2 py-1 text-[10px] font-bold text-green-700">PROCESSED</span>
                        ) : (
                          <span className="rounded-full bg-amber-50 px-2 py-1 text-[10px] font-bold text-amber-700">PENDING</span>
                        )}
                      </td>
                      <td className="py-3 text-right text-gray-500">
                        {new Date(doc.upload_date).toLocaleDateString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
