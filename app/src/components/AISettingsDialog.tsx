import { useEffect, useMemo, useState } from 'react';
import { Activity, Bot, Eye, EyeOff, Loader2, Save, Settings2 } from 'lucide-react';
import { toast } from 'sonner';

import { aiConfigApi, type AIConfig, type AIConfigTestResponse } from '../services/api';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';

type FormState = {
  base_url: string;
  model_name: string;
  api_key: string;
  enable_web_search: boolean;
  web_search_api_key: string;
};

const EMPTY_FORM: FormState = {
  base_url: '',
  model_name: '',
  api_key: '',
  enable_web_search: false,
  web_search_api_key: '',
};

export default function AISettingsDialog() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [config, setConfig] = useState<AIConfig | null>(null);
  const [testResult, setTestResult] = useState<AIConfigTestResponse | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);

  useEffect(() => {
    if (!open) {
      return;
    }

    const run = async () => {
      setTestResult(null);
      setLoading(true);
      try {
        const result = await aiConfigApi.getConfig();
        setConfig(result);
        setForm({
          base_url: result.base_url || '',
          model_name: result.model_name || '',
          api_key: '',
          enable_web_search: result.enable_web_search || false,
          web_search_api_key: '',
        });
      } catch (error) {
        toast.error('读取 AI 配置失败');
      } finally {
        setLoading(false);
      }
    };

    run();
  }, [open]);

  const maskedKeyText = useMemo(() => {
    if (!config?.has_api_key) {
      return '未配置';
    }
    return config.masked_api_key || '已配置';
  }, [config]);

  const maskedWebSearchKeyText = useMemo(() => {
    if (!config?.has_web_search_api_key) {
      return '未配置';
    }
    return config.masked_web_search_api_key || '已配置';
  }, [config]);

  const updateField = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setTestResult(null);
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleTestConnection = async () => {
    if (!form.base_url.trim()) {
      toast.error('请填写 Base URL');
      return;
    }
    if (!form.model_name.trim()) {
      toast.error('请填写 Model');
      return;
    }
    if (!form.api_key.trim() && !config?.has_api_key) {
      toast.error('请填写 API Key');
      return;
    }

    setTesting(true);
    setTestResult(null);
    try {
      const result = await aiConfigApi.testConnection(form);
      setTestResult(result);
      if (result.success) {
        toast.success('AI 接口连通性正常');
      } else {
        toast.error('AI 接口连通性测试失败');
      }
    } catch (error) {
      toast.error('AI 接口连通性测试失败');
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (!form.base_url.trim()) {
      toast.error('请填写 Base URL');
      return;
    }
    if (!form.model_name.trim()) {
      toast.error('请填写 Model');
      return;
    }

    setSaving(true);
    try {
      const result = await aiConfigApi.updateConfig(form);
      setConfig(result);
      setForm((prev) => ({ ...prev, api_key: '' }));
      toast.success('AI 配置已保存');
    } catch (error) {
      toast.error('保存 AI 配置失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          className="border-amber-500/30 bg-amber-500/10 text-amber-200 hover:bg-amber-500/20 hover:text-amber-100"
        >
          <Settings2 className="mr-2 h-4 w-4" />
          AI 设置
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl border border-zinc-800 bg-[#111111] text-zinc-100">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-lg font-semibold text-zinc-50">
            <Bot className="h-5 w-5 text-amber-400" />
            OpenAI 兼容接口设置
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex min-h-[240px] items-center justify-center">
            <Loader2 className="h-5 w-5 animate-spin text-amber-400" />
          </div>
        ) : (
          <div className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="base_url" className="text-zinc-300">
                Base URL
              </Label>
              <Input
                id="base_url"
                value={form.base_url}
                onChange={(event) => updateField('base_url', event.target.value)}
                placeholder="https://api.openai.com/v1"
                className="border-zinc-800 bg-zinc-950 text-zinc-100"
              />
              <p className="text-xs text-zinc-500">
                所有 AI 分析模块都会使用这里配置的 OpenAI 兼容接口。
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="model_name" className="text-zinc-300">
                Model
              </Label>
              <Input
                id="model_name"
                value={form.model_name}
                onChange={(event) => updateField('model_name', event.target.value)}
                placeholder="gpt-4o-mini / deepseek-chat / glm-4.5"
                className="border-zinc-800 bg-zinc-950 text-zinc-100"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="api_key" className="text-zinc-300">
                  API Key
                </Label>
                <span className="text-xs text-zinc-500">当前：{maskedKeyText}</span>
              </div>
              <div className="relative">
                <Input
                  id="api_key"
                  type={showKey ? 'text' : 'password'}
                  value={form.api_key}
                  onChange={(event) => updateField('api_key', event.target.value)}
                  placeholder="留空则保留现有 key"
                  className="border-zinc-800 bg-zinc-950 pr-10 text-zinc-100"
                />
                <button
                  type="button"
                  onClick={() => setShowKey((prev) => !prev)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 transition-colors hover:text-zinc-300"
                >
                  {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between rounded-md border border-zinc-800 bg-zinc-950/70 px-4 py-3">
              <div>
                <div className="text-sm font-medium text-zinc-200">启用 Tavily Web Search</div>
                <div className="text-xs text-zinc-500">
                  Agent 会先通过 Tavily 搜索真实网页结果，再交给模型分析
                </div>
              </div>
              <Switch
                checked={form.enable_web_search}
                onCheckedChange={(checked) => updateField('enable_web_search', checked)}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="web_search_api_key" className="text-zinc-300">
                  Tavily API Key
                </Label>
                <span className="text-xs text-zinc-500">当前：{maskedWebSearchKeyText}</span>
              </div>
              <div className="relative">
                <Input
                  id="web_search_api_key"
                  type={showKey ? 'text' : 'password'}
                  value={form.web_search_api_key}
                  onChange={(event) => updateField('web_search_api_key', event.target.value)}
                  placeholder="留空则保留现有 Tavily key"
                  className="border-zinc-800 bg-zinc-950 pr-10 text-zinc-100"
                />
                <button
                  type="button"
                  onClick={() => setShowKey((prev) => !prev)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 transition-colors hover:text-zinc-300"
                >
                  {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {testResult ? (
              <div
                className={`break-words rounded-md border px-4 py-3 text-sm ${
                  testResult.success
                    ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200'
                    : 'border-red-500/30 bg-red-500/10 text-red-200'
                }`}
              >
                <div className="font-medium">{testResult.message}</div>
                <div className="mt-1 text-xs opacity-80">
                  {testResult.model_name}
                  {typeof testResult.latency_ms === 'number' ? ` · ${testResult.latency_ms} ms` : ''}
                  {testResult.response_preview ? ` · ${testResult.response_preview}` : ''}
                </div>
              </div>
            ) : null}

            <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
              <Button
                variant="outline"
                onClick={handleTestConnection}
                disabled={testing || saving}
                className="border-emerald-500/30 bg-emerald-500/10 text-emerald-200 hover:bg-emerald-500/20 hover:text-emerald-100"
              >
                {testing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Activity className="mr-2 h-4 w-4" />}
                连通性测试
              </Button>
              <Button
                onClick={handleSave}
                disabled={saving || testing}
                className="bg-amber-500 text-black hover:bg-amber-400"
              >
                {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                保存配置
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
