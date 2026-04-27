import { useEffect, useMemo, useState, useRef } from 'react';
import { useLocation, useSearchParams } from 'react-router-dom';
import AppLayout from '../components/AppLayout';
import MessageBubble from '../components/MessageBubble';
import { useAuth } from '../context/AuthContext';
import { queryRag } from '../services/ragService';
import { canAccessDepartment } from '../utils/roles';
import { logError, logInfo } from '../utils/logger';
import { trackEvent, getChatHistory, appendChatHistory } from '../firebase';

function toBulletText(raw) {
  const text = (raw || '').toString().trim();
  if (!text) return '- No response received.';
  return text;
}

export default function QueryPage() {
  const { backendUser } = useAuth();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const initialDept = location.state?.department || searchParams.get('dept') || backendUser?.departments?.[0] || '';
  const [department, setDepartment] = useState(initialDept);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);

  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const [showScrollButton, setShowScrollButton] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
    setShowScrollButton(!isNearBottom);
  };

  const departments = useMemo(() => backendUser?.departments || [], [backendUser]);

  useEffect(() => {
    const targetDept = location.state?.department || searchParams.get('dept');
    if (targetDept && departments.includes(targetDept)) {
        setDepartment(targetDept);
    } else if (!department && departments.length > 0) {
      setDepartment(departments[0]);
    }
  }, [department, departments, location.state, searchParams]);

  const handleDepartmentChange = (e) => {
    const newDept = e.target.value;
    setDepartment(newDept);
    setSearchParams({ dept: newDept });
  };

  // Load chat history from Firestore strictly per-department
  useEffect(() => {
    let active = true;
    const fetchHistory = async () => {
      if (!department) return;
      
      const welcomeMessage = {
        id: 'welcome',
        sender: 'assistant',
        text: `- Welcome to ${department.toUpperCase()} department documents.\n- Responses are role-restricted.`,
        timestamp: new Date().toISOString()
      };

      setMessages([welcomeMessage]); // Clear UI temporarily
      
      const firestoreHistory = await getChatHistory(department);
      
      if (active && firestoreHistory.length > 0) {
        // Map Firestore history to UI format
        const uiHistory = firestoreHistory.map((entry, i) => ({
          id: `hist_${i}`,
          sender: entry.role,
          text: entry.content,
          timestamp: entry.timestamp
        }));
        setMessages([welcomeMessage, ...uiHistory]);
      }
    };
    
    fetchHistory();
    return () => { active = false; };
  }, [department]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!query.trim()) return;

    if (!canAccessDepartment(backendUser?.role, department)) {
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), sender: 'assistant', text: '- You do not have permission to access this information.' },
      ]);
      return;
    }

    const userText = query.trim();
    const timestamp = new Date().toISOString();
    
    const userMessage = { id: crypto.randomUUID(), sender: 'user', text: userText, timestamp };
    const placeholder = { id: crypto.randomUUID(), sender: 'assistant', text: '- Thinking...' };

    // Extract recent history for context
    const historyStrings = messages
      .filter((m) => m.sender === 'user' && m.id !== 'welcome')
      .map((m) => m.text)
      .slice(-3); // Last 3 user queries for context

    setMessages((prev) => [...prev, userMessage, placeholder]);
    setQuery('');
    setLoading(true);

    try {
      const response = await queryRag({ query: userText, department, history: historyStrings });
      logInfo('Query response:', response);

      let responseText =
        response?.response ||
        response?.answer ||
        response?.message ||
        'No response content.';

      // Parse suggestions: handles [[Suggestions: Q1 | Q2 | Q3]] and bare [[Q1? | Q2? | Q3?]]
      let suggestions = [];
      let suggestionMatch = responseText.match(/\[\[Suggestions:\s*([\s\S]*?)\s*\]\]/i);
      if (!suggestionMatch) {
        // Fallback: bare [[Q1? | Q2? | Q3?]] (must contain | to be suggestions)
        suggestionMatch = responseText.match(/\[\[([^\[\]]*?\|[^\[\]]*?)\]\]/);
      }
      if (suggestionMatch) {
        suggestions = suggestionMatch[1].split('|').map(s => s.trim()).filter(Boolean);
        responseText = responseText.replace(suggestionMatch[0], '').trim();
      }
      // Strip "Follow-up questions:" noise line
      responseText = responseText.replace(/follow[\s-]*up\s+questions?\s*:?\s*$/im, '').trim();

      const normalized = toBulletText(responseText);
      const sources = response?.sources || [];
      const metrics = response?.metrics || {};

      // Track detailed query activity in Firebase Analytics
      trackEvent('document_query', { 
        department, 
        query_text: userText,
        response_preview: normalized,
        timestamp,
        metrics // Include benchmarking data
      });

      // Append entirely new interactions strictly to this department's Firestore history
      await appendChatHistory(department, [
        { role: 'user', content: userText, timestamp },
        { role: 'assistant', content: normalized, timestamp: new Date().toISOString() }
      ]);

      setMessages((prev) =>
        prev.map((msg) => (msg.id === placeholder.id ? { 
          ...msg, 
          text: normalized, 
          sources, 
          suggestions,
          isGraph: department.toLowerCase() === 'graph'
        } : msg))
      );
    } catch (err) {
      logError('Query failed:', err);
      const apiMessage = err?.response?.data?.error || err?.response?.data?.detail;

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === placeholder.id
            ? { ...msg, text: `- ${apiMessage || 'API failure while generating response.'}` }
            : msg
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
    // Trigger submit manually or let user click send
    // For better UX, we'll just set it and focus the input
    document.getElementById('query-input')?.focus();
  };

  return (
    <AppLayout>
      <div className="flex h-[calc(100vh-12rem)] flex-col rounded-xl border border-border bg-white relative">
        <div className="border-b border-border px-4 py-3">
          <div className="flex items-center justify-between gap-3">
            <h1 className="text-sm font-semibold">Document Query</h1>
            <select
              className="input max-w-[180px] py-2"
              value={department}
              onChange={handleDepartmentChange}
            >
              {departments.map((dept) => (
                <option key={dept} value={dept}>{dept.toUpperCase()}</option>
              ))}
            </select>
          </div>
        </div>

        <div 
          className="flex-1 space-y-3 overflow-y-auto p-4"
          ref={chatContainerRef}
          onScroll={handleScroll}
        >
          {messages.map((message) => (
            <MessageBubble 
              key={message.id} 
              sender={message.sender} 
              text={message.text} 
              sources={message.sources}
              suggestions={message.suggestions}
              onSuggestionClick={handleSuggestionClick}
              isGraph={message.isGraph}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {showScrollButton && (
          <button
            onClick={scrollToBottom}
            className="absolute bottom-24 right-8 p-3 bg-black text-white rounded-full shadow-xl hover:bg-gray-800 transition-all hover:scale-110 z-50 flex items-center justify-center animate-in fade-in zoom-in duration-200"
            title="Scroll to latest message"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 5v14M19 12l-7 7-7-7" />
            </svg>
          </button>
        )}

        <form onSubmit={handleSubmit} className="border-t border-border p-4">
          <div className="flex gap-2">
            <input
              id="query-input"
              className="input"
              placeholder="Ask about documents..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button className="btn-primary px-5" type="submit" disabled={loading}>
              {loading ? '...' : 'Send'}
            </button>
          </div>
        </form>
      </div>
    </AppLayout>
  );
}
