import { useEffect, useState } from 'react';
import AppLayout from '../components/AppLayout';
import { useAuth } from '../context/AuthContext';
import { db } from '../firebase';
import { collection, getDocs, query, limit, orderBy } from 'firebase/firestore';
import { listDocuments } from '../services/uploadService';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  LineChart, Line, AreaChart, Area
} from 'recharts';
import { ROLE } from '../utils/roles';

export default function DashboardPage() {
  const { backendUser } = useAuth();
  const departments = backendUser?.departments || [];
  const isAdmin = backendUser?.role === ROLE.ADMINISTRATOR;

  const [stats, setStats] = useState({
    deptData: [],
    benchmarkData: [],
    knowledgeGaps: [],
    timelineData: [],
    recentActivity: [],
    documents: [],
    totalTokens: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [backendUser]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // 1. Fetch Firestore Analytics (Admins only for global, or limited)
      await fetchAnalytics();
      
      // 2. Fetch Document List (Scoped by Backend RBAC)
      const docs = await listDocuments();
      setStats(prev => ({ ...prev, documents: docs }));
    } catch (err) {
      console.error('Data fetch failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    if (!isAdmin) return;
    try {
      const q = query(collection(db, 'user_activity_logs'), orderBy('server_timestamp', 'desc'), limit(100));
      const querySnapshot = await getDocs(q);
      const logs = querySnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));

      const deptCounts = {};
      const timelineMap = {};
      let totalRetrieval = 0;
      let totalLLM = 0;
      let queryCount = 0;
      let totalTokens = 0;

      logs.forEach(log => {
        if (log.event_name === 'document_query' && log.department) {
          deptCounts[log.department] = (deptCounts[log.department] || 0) + 1;
          const date = log.timestamp ? new Date(log.timestamp).toLocaleDateString() : 'Unknown';
          timelineMap[date] = (timelineMap[date] || 0) + 1;

          if (log.metrics) {
            totalRetrieval += log.metrics.retrieval_time || 0;
            totalLLM += (log.metrics.total_time || 0) - (log.metrics.retrieval_time || 0);
            queryCount++;
            totalTokens += (log.query_text?.split(' ').length || 0) + (log.response_preview?.split(' ').length || 0);
          }
        }
      });

      const deptData = Object.entries(deptCounts).map(([name, value]) => ({ name: name.toUpperCase(), value }));
      const benchmarkData = queryCount > 0 ? [
        { name: 'Retrieval', value: parseFloat((totalRetrieval / queryCount).toFixed(3)) },
        { name: 'LLM Gen', value: parseFloat((totalLLM / queryCount).toFixed(3)) }
      ] : [];
      const timelineData = Object.entries(timelineMap).map(([date, count]) => ({ date, count })).reverse();
      const gaps = logs
        .filter(log => log.event_name === 'document_query' && (log.response_preview?.includes('Not available') || log.response_preview?.includes('not available')))
        .slice(0, 5)
        .map(log => ({ query: log.query_text, dept: log.department }));

      setStats(prev => ({
        ...prev,
        deptData,
        knowledgeGaps: gaps,
        benchmarkData,
        timelineData,
        recentActivity: logs.slice(0, 8),
        totalTokens: Math.round(totalTokens * 1.3)
      }));
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    }
  };

  return (
    <AppLayout>
      <div className="space-y-6 pb-12">
        {/* KPI Bar */}
        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="card border-l-4 border-l-primary">
            <p className="text-[10px] uppercase font-bold text-gray-400">Total Tokens Processed</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">{stats.totalTokens.toLocaleString()}</p>
          </div>
          <div className="card border-l-4 border-l-green-500">
            <p className="text-[10px] uppercase font-bold text-gray-400">Avg. Response Time</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">
              {(stats.benchmarkData.reduce((acc, curr) => acc + curr.value, 0)).toFixed(2)}s
            </p>
          </div>
          <div className="card border-l-4 border-l-amber-500">
            <p className="text-[10px] uppercase font-bold text-gray-400">Knowledge Gaps</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">{stats.knowledgeGaps.length}</p>
          </div>
          <div className="card border-l-4 border-l-purple-500">
            <p className="text-[10px] uppercase font-bold text-gray-400">Total Documents</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">{stats.documents.length}</p>
          </div>
        </section>

        {isAdmin && (
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="card lg:col-span-2">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-base font-semibold">Query Activity Timeline</h2>
                <span className="text-[10px] bg-soft px-2 py-1 rounded-full font-bold text-primary">LIVE UPDATES</span>
              </div>
              <div className="h-64 w-full">
                {loading ? (
                  <div className="h-full w-full flex items-center justify-center animate-pulse bg-soft rounded-xl"></div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={stats.timelineData}>
                      <defs>
                        <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.1}/>
                          <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F0F0F0" />
                      <XAxis dataKey="date" fontSize={10} axisLine={false} tickLine={false} />
                      <YAxis fontSize={10} axisLine={false} tickLine={false} />
                      <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                      <Area type="monotone" dataKey="count" stroke="#3B82F6" strokeWidth={2} fillOpacity={1} fill="url(#colorCount)" />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            <div className="card">
              <h2 className="text-base font-semibold mb-4">Latency Benchmarks</h2>
              <div className="space-y-6">
                {stats.benchmarkData.map((item, idx) => (
                  <div key={idx}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-medium text-gray-500">{item.name}</span>
                      <span className="font-bold text-primary">{item.value}s</span>
                    </div>
                    <div className="h-1.5 w-full bg-soft rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all duration-1000 ${idx === 0 ? 'bg-blue-500' : 'bg-purple-500'}`}
                        style={{ width: `${Math.min((item.value / 2) * 100, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
                <div className="pt-4 border-t border-border">
                  <p className="text-[10px] font-bold text-gray-400 uppercase mb-2">System Status</p>
                  <div className="flex gap-2">
                    <div className="flex-1 text-center p-2 rounded-lg bg-green-50 border border-green-100">
                      <p className="text-[16px]">✅</p>
                      <p className="text-[9px] font-bold text-green-700">RAG ENGINE</p>
                    </div>
                    <div className="flex-1 text-center p-2 rounded-lg bg-green-50 border border-green-100">
                      <p className="text-[16px]">⚡</p>
                      <p className="text-[9px] font-bold text-green-700">GROQ-LLM</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Departmental Inventory Section */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-base font-semibold">Departmental Document Inventory</h2>
            <p className="text-[11px] text-gray-400">Total Records: {stats.documents.length}</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-[10px] uppercase font-bold text-gray-400 border-b border-border">
                  <th className="pb-3">Document Name</th>
                  <th className="pb-3">Department</th>
                  <th className="pb-3">Contributor</th>
                  <th className="pb-3">Status</th>
                  <th className="pb-3 text-right">Upload Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {stats.documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-soft/50 transition-colors">
                    <td className="py-4 font-medium text-gray-900 pr-4">
                      <div className="flex items-center gap-2">
                        <span className="text-primary">📄</span>
                        {doc.filename}
                      </div>
                    </td>
                    <td className="py-4">
                      <span className="px-2 py-0.5 rounded-full bg-primary/5 text-[10px] font-bold uppercase text-primary">
                        {doc.department}
                      </span>
                    </td>
                    <td className="py-4 text-gray-600">{doc.uploaded_by_username || 'System'}</td>
                    <td className="py-4">
                      {doc.is_processed ? (
                        <span className="flex items-center gap-1.5 text-[11px] font-medium text-green-600">
                          <span className="h-1.5 w-1.5 rounded-full bg-green-600"></span>
                          Indexed
                        </span>
                      ) : (
                        <span className="flex items-center gap-1.5 text-[11px] font-medium text-amber-600">
                          <span className="h-1.5 w-1.5 rounded-full bg-amber-600 animate-pulse"></span>
                          Pending
                        </span>
                      )}
                    </td>
                    <td className="py-4 text-right text-xs text-gray-400">
                      {new Date(doc.upload_date).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
                {stats.documents.length === 0 && !loading && (
                  <tr>
                    <td colSpan="5" className="py-12 text-center text-gray-400 italic">No documents found in inventory.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {isAdmin && (
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="card">
              <h2 className="text-base font-semibold mb-4">Live Activity Feed</h2>
              <div className="space-y-4">
                {stats.recentActivity.map((log) => (
                  <div key={log.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-soft transition-colors">
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-gray-800 truncate max-w-[250px]">{log.query_text}</span>
                      <span className="text-[10px] text-gray-400">{new Date(log.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <span className="text-[10px] font-mono text-primary font-bold">{log.metrics?.total_time}s</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <h2 className="text-base font-semibold mb-4 text-amber-600">Unanswered Queries</h2>
              <div className="space-y-3">
                {stats.knowledgeGaps.map((gap, i) => (
                  <div key={i} className="p-3 rounded-xl bg-amber-50 border border-amber-100">
                    <p className="text-xs font-bold text-gray-800">"{gap.query}"</p>
                    <p className="mt-2 text-[9px] font-bold uppercase text-amber-600">{gap.dept}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
