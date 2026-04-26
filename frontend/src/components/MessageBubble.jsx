import { jsPDF } from 'jspdf';

export default function MessageBubble({ 
  sender, 
  text, 
  sources = [], 
  suggestions = [], 
  onSuggestionClick,
  isGraph = false
}) {
  const isUser = sender === 'user';

  const handleDownloadPDF = () => {
    const doc = new jsPDF();
    const timestamp = new Date().toLocaleString();
    const title = isGraph ? 'IntraDoc Intelligence - Unified Profile' : 'IntraDoc Intelligence - Document Insights';
    
    doc.setFontSize(20);
    doc.text(title, 20, 20);
    
    doc.setFontSize(10);
    doc.text(`Generated on: ${timestamp}`, 20, 30);
    doc.text('------------------------------------------------------------', 20, 35);
    
    doc.setFontSize(12);
    const splitText = doc.splitTextToSize(text, 170);
    doc.text(splitText, 20, 45);
    
    if (sources.length > 0) {
      const yPos = 45 + (splitText.length * 7) + 10;
      doc.setFontSize(14);
      doc.text('Sources Verified:', 20, yPos);
      doc.setFontSize(10);
      sources.forEach((src, idx) => {
        doc.text(`- ${src.filename} (${src.department.toUpperCase()})`, 25, yPos + 10 + (idx * 5));
      });
    }
    
    doc.save(`IntraDoc_Response_${new Date().getTime()}.pdf`);
  };

  return (
    <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} mb-4`}>
      <div
        className={`max-w-2xl rounded-xl border px-4 py-3 text-sm leading-relaxed relative ${
          isUser ? 'border-border bg-[#F8F8F8] text-text' : 'border-border bg-soft text-text'
        }`}
      >
        <div className="flex items-center justify-between gap-4 mb-1">
          <p className="text-[11px] font-medium uppercase tracking-wide text-gray-500">
            {isUser ? 'You' : 'Assistant'}
          </p>
          {!isUser && (
            <button 
              onClick={handleDownloadPDF}
              className="text-base hover:scale-110 transition-transform opacity-60 hover:opacity-100 p-0.5"
              title="Download as PDF"
            >
              📥
            </button>
          )}
        </div>
        <div className="space-y-1 whitespace-pre-wrap">
          {text}
        </div>

        {sources.length > 0 && (
          <div className="mt-3 border-t border-border pt-2">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">Sources</p>
            <div className="mt-1 flex flex-wrap gap-2">
              {sources.map((src, idx) => (
                <div 
                  key={idx} 
                  className="flex items-center gap-1.5 rounded-lg border border-border bg-white px-2 py-1 text-[11px] text-gray-600 shadow-sm"
                >
                  <span className="h-2 w-2 rounded-full bg-primary/40"></span>
                  {src.filename}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {!isUser && suggestions.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2 max-w-2xl">
          {suggestions.map((suggestion, idx) => (
            <button
              key={idx}
              onClick={() => onSuggestionClick(suggestion)}
              className="rounded-full border border-primary/20 bg-primary/5 px-3 py-1.5 text-xs text-primary transition-all hover:bg-primary/10 hover:shadow-sm"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
