import { useCallback, useEffect, useMemo, useState } from 'react';
import { Activity, AlertTriangle, CheckCircle2, Loader2, RefreshCw, XCircle } from 'lucide-react';
import { toast } from 'sonner';

import { dataSourceApi, type DataSourceCheck, type DataSourceStatusResponse } from '../services/api';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';

const statusStyles = {
  ok: {
    label: '正常',
    icon: CheckCircle2,
    className: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  },
  warning: {
    label: '注意',
    icon: AlertTriangle,
    className: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
  },
  error: {
    label: '异常',
    icon: XCircle,
    className: 'border-red-500/30 bg-red-500/10 text-red-300',
  },
} satisfies Record<DataSourceCheck['status'], { label: string; icon: typeof CheckCircle2; className: string }>;

const overallText = {
  ok: '全部正常',
  warning: '部分注意',
  degraded: '存在异常',
} satisfies Record<DataSourceStatusResponse['overall_status'], string>;

function StatusPill({ status }: { status: DataSourceCheck['status'] }) {
  const style = statusStyles[status];
  const Icon = style.icon;

  return (
    <span className={`inline-flex shrink-0 items-center gap-1 rounded-full border px-2 py-0.5 text-xs ${style.className}`}>
      <Icon className="h-3.5 w-3.5" />
      {style.label}
    </span>
  );
}

function SourceRow({ check }: { check: DataSourceCheck }) {
  const sampleText = useMemo(() => JSON.stringify(check.sample || {}, null, 2), [check.sample]);

  return (
    <div className="rounded-md border border-zinc-800 bg-zinc-950/70 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold text-zinc-100">{check.name}</h3>
            <StatusPill status={check.status} />
          </div>
          <p className="mt-1 text-xs text-zinc-500">{check.source}</p>
        </div>
        <div className="shrink-0 text-xs text-zinc-500">{check.latency_ms} ms</div>
      </div>

      <p className="mt-3 text-sm leading-6 text-zinc-300">{check.message}</p>

      {sampleText !== '{}' ? (
        <details className="mt-3">
          <summary className="cursor-pointer text-xs text-zinc-500 transition-colors hover:text-zinc-300">
            样例数据
          </summary>
          <pre className="mt-2 max-h-40 overflow-auto rounded bg-black/40 p-3 text-xs leading-5 text-zinc-400">
            {sampleText}
          </pre>
        </details>
      ) : null}
    </div>
  );
}

export default function DataSourceStatusDialog() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DataSourceStatusResponse | null>(null);

  const runCheck = useCallback(async () => {
    setLoading(true);
    try {
      const response = await dataSourceApi.checkStatus();
      setResult(response);
    } catch (error) {
      toast.error('数据源检测失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!open || result) {
      return;
    }
    runCheck();
  }, [open, result, runCheck]);

  const summary = result?.summary;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          aria-label="数据源检测"
          className="border-emerald-500/30 bg-emerald-500/10 text-emerald-200 hover:bg-emerald-500/20 hover:text-emerald-100"
        >
          <Activity className="h-4 w-4 sm:mr-2" />
          <span className="hidden sm:inline">数据源检测</span>
        </Button>
      </DialogTrigger>

      <DialogContent className="max-h-[86vh] max-w-4xl overflow-hidden border border-zinc-800 bg-[#111111] text-zinc-100">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-lg font-semibold text-zinc-50">
            <Activity className="h-5 w-5 text-emerald-400" />
            数据源状态检测
          </DialogTitle>
        </DialogHeader>

        <div className="max-h-[calc(86vh-96px)] space-y-5 overflow-y-auto pr-1">
          <div className="flex flex-col gap-3 rounded-md border border-zinc-800 bg-zinc-950/70 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="text-sm text-zinc-500">整体状态</div>
              <div className="mt-1 text-2xl font-semibold text-zinc-50">
                {result ? overallText[result.overall_status] : loading ? '检测中' : '未检测'}
              </div>
              {result ? <div className="mt-1 text-xs text-zinc-500">检测时间：{result.checked_at}</div> : null}
            </div>

            <Button
              onClick={runCheck}
              disabled={loading}
              className="w-full bg-emerald-500 text-black hover:bg-emerald-400 sm:w-auto"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
              重新检测
            </Button>
          </div>

          {summary ? (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div className="rounded-md border border-zinc-800 bg-zinc-950/70 p-3">
                <div className="text-xs text-zinc-500">总数</div>
                <div className="mt-1 text-xl font-semibold text-zinc-100">{summary.total}</div>
              </div>
              <div className="rounded-md border border-emerald-500/20 bg-emerald-500/10 p-3">
                <div className="text-xs text-emerald-300/80">正常</div>
                <div className="mt-1 text-xl font-semibold text-emerald-300">{summary.ok}</div>
              </div>
              <div className="rounded-md border border-amber-500/20 bg-amber-500/10 p-3">
                <div className="text-xs text-amber-300/80">注意</div>
                <div className="mt-1 text-xl font-semibold text-amber-300">{summary.warning}</div>
              </div>
              <div className="rounded-md border border-red-500/20 bg-red-500/10 p-3">
                <div className="text-xs text-red-300/80">异常</div>
                <div className="mt-1 text-xl font-semibold text-red-300">{summary.error}</div>
              </div>
            </div>
          ) : null}

          {loading && !result ? (
            <div className="flex min-h-[260px] items-center justify-center rounded-md border border-zinc-800 bg-zinc-950/70">
              <Loader2 className="h-6 w-6 animate-spin text-emerald-400" />
            </div>
          ) : null}

          {result ? (
            <div className="space-y-3">
              {result.checks.map((check) => (
                <SourceRow key={`${check.category}-${check.name}-${check.source}`} check={check} />
              ))}
            </div>
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
