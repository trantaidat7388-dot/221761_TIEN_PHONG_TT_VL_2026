import { CheckCircle2, Clock, XCircle } from 'lucide-react';

const StatusBadge = ({ status }) => {
  const configMap = {
    completed: { icon: CheckCircle2, cls: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' },
    pending: { icon: Clock, cls: 'bg-amber-500/10 text-amber-300 border-amber-500/20' },
    failed: { icon: XCircle, cls: 'bg-red-500/10 text-red-300 border-red-500/20' },
    success: { icon: CheckCircle2, cls: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' },
  };
  const cfg = configMap[status] || configMap.pending;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-xs ${cfg.cls}`}>
      <Icon className="h-3 w-3" /> {status || 'unknown'}
    </span>
  );
};

export default StatusBadge;
