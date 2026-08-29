import { useEffect, useRef, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const VARIANTS = [
  { key: 'baseline', label: 'Baseline', color: '#64748b' },
  { key: 'tool_agent', label: 'Tool Agent', color: '#3b82f6' },
  { key: 'self_improving', label: 'Self-Improving', color: '#22c55e' },
]

function variantLabel(key) {
  return VARIANTS.find((v) => v.key === key)?.label ?? key
}

function Check({ ok }) {
  return (
    <span className={ok ? 'text-green-400' : 'text-red-400'}>
      {ok ? '✓' : '✗'}
    </span>
  )
}

function buildLeaderboardData(results) {
  const byGeneration = {}
  for (const r of results) {
    const gen = r.generation
    byGeneration[gen] ??= {}
    byGeneration[gen][r.variant] ??= []
    byGeneration[gen][r.variant].push(r.score)
  }

  return Object.keys(byGeneration)
    .sort((a, b) => Number(a) - Number(b))
    .map((gen) => {
      const row = { generation: `Gen ${gen}` }
      for (const { key } of VARIANTS) {
        const scores = byGeneration[gen][key] ?? []
        row[key] = scores.length
          ? Number((scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(2))
          : 0
      }
      return row
    })
}

function buildTableRows(results) {
  const latest = {}
  for (const r of results) {
    const key = `${r.challenge}::${r.variant}`
    const existing = latest[key]
    if (!existing || r.generation >= existing.generation) {
      latest[key] = r
    }
  }
  return Object.values(latest).sort(
    (a, b) =>
      a.challenge.localeCompare(b.challenge) ||
      a.variant.localeCompare(b.variant)
  )
}

function buildActivityLog(results) {
  return results
    .slice()
    .reverse()
    .slice(0, 50)
    .map((r, i) => ({
      id: `${r.generation}-${r.variant}-${r.challenge}-${i}`,
      text: `[Gen ${r.generation}] ${variantLabel(r.variant)} finished "${r.challenge}" — score ${r.score?.toFixed(1)}/10.0, ${r.tool_calls} tool call${r.tool_calls === 1 ? '' : 's'}`,
    }))
}

export default function App() {
  const [results, setResults] = useState([])
  const [runStatus, setRunStatus] = useState('idle')
  const pollRef = useRef(null)

  const fetchResults = async () => {
    try {
      const res = await fetch(`${API_BASE}/results`)
      const data = await res.json()
      setResults(data)
    } catch (err) {
      console.error('Failed to fetch results', err)
    }
  }

  useEffect(() => {
    fetchResults()
    pollRef.current = setInterval(fetchResults, 2000)
    return () => clearInterval(pollRef.current)
  }, [])

  const startRun = async () => {
    setRunStatus('starting')
    try {
      const res = await fetch(`${API_BASE}/run`, { method: 'POST' })
      if (res.status === 409) {
        setRunStatus('running')
        return
      }
      setRunStatus('running')
    } catch (err) {
      console.error('Failed to start run', err)
      setRunStatus('idle')
    }
  }

  const leaderboardData = buildLeaderboardData(results)
  const tableRows = buildTableRows(results)
  const activityLog = buildActivityLog(results)

  const totalGenerations = leaderboardData.length
  const winner =
    totalGenerations > 0
      ? VARIANTS.reduce((best, v) => {
          const last = leaderboardData[leaderboardData.length - 1]
          return last[v.key] > (last[best.key] ?? -Infinity) ? v : best
        }, VARIANTS[0])
      : null

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">CyberAgent Arena</h1>
          <p className="text-slate-400 text-sm">
            {results.length} result{results.length === 1 ? '' : 's'} recorded
            {winner && (
              <>
                {' '}
                · Leading: <span className="text-green-400">{winner.label}</span>
              </>
            )}
          </p>
        </div>
        <button
          onClick={startRun}
          disabled={runStatus === 'starting'}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg transition"
        >
          {runStatus === 'running' ? 'Running…' : 'Run Arena'}
        </button>
      </header>

      <section className="bg-slate-900 rounded-xl p-4 border border-slate-800">
        <h2 className="text-lg font-semibold mb-3">Leaderboard</h2>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={leaderboardData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="generation" stroke="#94a3b8" />
              <YAxis domain={[0, 10]} stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #334155' }}
              />
              <Legend />
              {VARIANTS.map((v) => (
                <Bar key={v.key} dataKey={v.key} name={v.label} fill={v.color} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <h2 className="text-lg font-semibold mb-3">Agent Activity Log</h2>
          <div className="h-80 overflow-y-auto space-y-1 font-mono text-xs">
            {activityLog.length === 0 && (
              <p className="text-slate-500">No activity yet — run the arena to begin.</p>
            )}
            {activityLog.map((entry) => (
              <div key={entry.id} className="text-slate-300 border-b border-slate-800 py-1">
                {entry.text}
              </div>
            ))}
          </div>
        </section>

        <section className="bg-slate-900 rounded-xl p-4 border border-slate-800">
          <h2 className="text-lg font-semibold mb-3">Challenge Results</h2>
          <div className="h-80 overflow-y-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-slate-400 border-b border-slate-800 sticky top-0 bg-slate-900">
                <tr>
                  <th className="py-2 pr-2">Challenge</th>
                  <th className="py-2 pr-2">Variant</th>
                  <th className="py-2 pr-2 text-center">Detect</th>
                  <th className="py-2 pr-2 text-center">File</th>
                  <th className="py-2 pr-2 text-center">Line</th>
                  <th className="py-2 pr-2 text-center">Sev</th>
                  <th className="py-2 text-right">Score</th>
                </tr>
              </thead>
              <tbody>
                {tableRows.map((r) => (
                  <tr key={`${r.challenge}-${r.variant}`} className="border-b border-slate-800/60">
                    <td className="py-2 pr-2">{r.challenge}</td>
                    <td className="py-2 pr-2 text-slate-400">{variantLabel(r.variant)}</td>
                    <td className="py-2 pr-2 text-center"><Check ok={r.correct_vuln_type} /></td>
                    <td className="py-2 pr-2 text-center"><Check ok={r.correct_file} /></td>
                    <td className="py-2 pr-2 text-center"><Check ok={r.correct_line} /></td>
                    <td className="py-2 pr-2 text-center"><Check ok={r.correct_severity} /></td>
                    <td className="py-2 text-right">{r.score?.toFixed(1)}</td>
                  </tr>
                ))}
                {tableRows.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-4 text-center text-slate-500">
                      No results yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  )
}
