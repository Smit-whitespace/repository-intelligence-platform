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
    <section className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Settings</h2>
        <p className="text-sm text-muted-foreground">
          Backend-supported application settings.
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-md border border-border bg-surface p-4">
          <h3 className="text-sm font-semibold">Theme</h3>
          <select
            value={theme}
            onChange={(event) => setTheme(event.target.value as ThemeMode)}
            className="mt-3 h-9 w-full rounded-md border border-border bg-background px-2 text-sm"
          >
            {themeOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
        <form
          className="rounded-md border border-border bg-surface p-4"
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
          <h3 className="text-sm font-semibold">Backend model</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Provider: {activeModel.data?.active_provider ?? status.data?.active_provider}
          </p>
          <div className="mt-3 flex flex-col gap-3 md:flex-row">
            <select
              value={modelValue}
              onChange={(event) => setSelectedModel(event.target.value)}
              className="h-9 min-w-0 flex-1 rounded-md border border-border bg-background px-2 text-sm"
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
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <Save className="mr-2 h-4 w-4" aria-hidden="true" />
              )}
              Save
            </Button>
          </div>
          {models.isError ? (
            <p className="mt-3 text-sm text-red-500">{models.error.message}</p>
          ) : null}
          {updateActiveModel.isError ? (
            <p className="mt-3 text-sm text-red-500">
              {updateActiveModel.error.message}
            </p>
          ) : null}
        </form>
      </div>
    </section>
  );
}
