import { ApiErrorState } from "@/components/common/ApiErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { Button } from "@/components/ui/Button";
import {
  useActiveModel,
  useModels,
  useSystemStatus,
  useUpdateActiveModel,
} from "@/lib/api/queries";
import { useThemeStore, type ThemeMode } from "@/stores/themeStore";
import { RefreshCw, Save } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

const themeOptions: ThemeMode[] = ["light", "dark", "system"];

export function SettingsPage() {
  const theme = useThemeStore((state) => state.theme);
  const setTheme = useThemeStore((state) => state.setTheme);
  const status = useSystemStatus();
  const activeModel = useActiveModel();
  const models = useModels();
  const updateActiveModel = useUpdateActiveModel();
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  if (status.isLoading || activeModel.isLoading) {
    return <LoadingState label="Loading settings" />;
  }

  if (status.isError) {
    return <ApiErrorState error={status.error} />;
  }

  if (activeModel.isError) {
    return <ApiErrorState error={activeModel.error} />;
  }

  const canSave =
    Boolean(selectedModel) &&
    selectedModel !== activeModel.data?.active_model &&
    !updateActiveModel.isPending;
  const modelValue =
    selectedModel ??
    activeModel.data?.active_model ??
    models.data?.models.at(0)?.name ??
    "";

  return (
    <section className="animate-fade-in space-y-8">
      <div>
        <h1 className="text-lg font-semibold text-[#F8FAFC]">Settings</h1>
        <p className="mt-1 text-sm text-[#7A8599]">
          Application configuration.
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Theme">
          <div className="mt-4 space-y-3">
            <div className="flex gap-2">
              {themeOptions.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setTheme(option)}
                  className={
                    theme === option
                      ? "flex-1 rounded-[var(--radius-sm)] border border-[#4F8CFF] bg-[rgba(79,140,255,0.08)] px-3 py-2 text-sm font-medium text-[#F8FAFC] transition"
                      : "flex-1 rounded-[var(--radius-sm)] border border-[rgba(255,255,255,0.1)] bg-transparent px-3 py-2 text-sm text-[#AAB4C5] transition hover:border-[rgba(255,255,255,0.2)] hover:text-[#F8FAFC]"
                  }
                >
                  {option.charAt(0).toUpperCase() + option.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </Panel>
        <Panel title="Backend model">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (!modelValue) {
                return;
              }
              updateActiveModel.mutate(
                {
                  model: modelValue,
                },
                {
                  onSuccess: () => {
                    setSelectedModel(null);
                    toast.success("Active model updated");
                  },
                },
              );
            }}
          >
            <p className="mt-1 text-sm text-[#7A8599]">
              Provider: {activeModel.data?.active_provider ?? status.data?.active_provider}
            </p>
            <div className="mt-4 flex flex-col gap-3 md:flex-row">
              <select
                value={modelValue}
                onChange={(event) => setSelectedModel(event.target.value)}
                className="h-9 min-w-0 flex-1 rounded-[var(--radius-sm)] border border-[rgba(255,255,255,0.1)] bg-[#0A0F1E] px-3 text-sm text-[#F8FAFC] outline-none transition focus:border-[#4F8CFF]/50"
              >
                {models.data?.models.length ? (
                  models.data.models.map((model) => (
                    <option key={model.name} value={model.name}>
                      {model.name}
                    </option>
                  ))
                ) : (
                  <option value="">No installed models</option>
                )}
              </select>
              <Button type="submit" disabled={!canSave}>
                {updateActiveModel.isPending ? (
                  <RefreshCw className="h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Save className="h-4 w-4" aria-hidden="true" />
                )}
                Save
              </Button>
            </div>
            {models.isError ? (
              <p className="mt-3 text-sm text-[#EF4444]">{models.error.message}</p>
            ) : null}
            {updateActiveModel.isError ? (
              <p className="mt-3 text-sm text-[#EF4444]">
                {updateActiveModel.error.message}
              </p>
            ) : null}
          </form>
        </Panel>
      </div>
    </section>
  );
}

type PanelProps = {
  title: string;
  children: React.ReactNode;
};

function Panel({ title, children }: PanelProps) {
  return (
    <section className="rounded-[var(--radius)] border border-[rgba(255,255,255,0.06)] bg-[#111827] p-5">
      <h3 className="text-sm font-semibold text-[#F8FAFC]">{title}</h3>
      {children}
    </section>
  );
}
