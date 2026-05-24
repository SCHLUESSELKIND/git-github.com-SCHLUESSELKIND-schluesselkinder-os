"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { instantiateAutomationRuleTemplate } from "../../../_lib/inference";
import type {
  CampaignAutomationRuleTemplate,
} from "../../../_lib/inference-types";

/**
 * S60 — Automation Rule Templates (client controls).
 *
 * Renders the curated catalogue with an INSTANTIATE button per template.
 * Templates create rule definitions only. No automation is executed.
 */
export function AutomationTemplateLibrary({
  campaignId,
  templates,
}: Readonly<{
  campaignId: string;
  templates: ReadonlyArray<CampaignAutomationRuleTemplate>;
}>) {
  return (
    <div className="space-y-1">
      {templates.map((template) => (
        <TemplateRow
          key={template.template_id}
          campaignId={campaignId}
          template={template}
        />
      ))}
    </div>
  );
}

function TemplateRow({
  campaignId,
  template,
}: Readonly<{
  campaignId: string;
  template: CampaignAutomationRuleTemplate;
}>) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [status, setStatus] = useState<"idle" | "ok" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleClick = () => {
    setStatus("idle");
    setErrorMsg(null);
    startTransition(async () => {
      try {
        await instantiateAutomationRuleTemplate(template.slug, {
          campaign_id: campaignId,
        });
        setStatus("ok");
        router.refresh();
      } catch (err) {
        setStatus("error");
        setErrorMsg(err instanceof Error ? err.message : "Unknown error");
      }
    });
  };

  return (
    <div
      className="flex flex-wrap items-center justify-between gap-3 border border-[color:var(--ss-border)] px-4 py-3"
      style={{ backgroundColor: "var(--ss-panel)" }}
    >
      <div className="flex max-w-2xl flex-col gap-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-[0.62rem] font-bold text-[color:var(--ss-text-primary)]">
            {template.name}
          </span>
          <span className="font-mono text-[0.45rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
            {template.category.replace(/_/g, " ")}
          </span>
        </div>
        {template.description && (
          <span className="font-mono text-[0.52rem] text-[color:var(--ss-text-muted)]">
            {template.description}
          </span>
        )}
        <div className="flex flex-wrap items-center gap-3 text-[color:var(--ss-text-muted)]">
          <span className="font-mono text-[0.48rem] uppercase tracking-widest">
            TRIGGER: {template.trigger}
          </span>
          <span className="font-mono text-[0.48rem] uppercase tracking-widest">
            ACTION: {template.action}
          </span>
        </div>
        {template.warnings.length > 0 && (
          <span className="font-mono text-[0.48rem] text-orange-400">
            {template.warnings.join(" · ")}
          </span>
        )}
      </div>
      <div className="flex flex-col items-end gap-1">
        <button
          type="button"
          onClick={handleClick}
          disabled={isPending || !template.enabled}
          className="border border-[color:var(--ss-accent)] px-2 py-1 font-mono text-[0.5rem] font-black uppercase tracking-widest text-[color:var(--ss-accent)] hover:bg-[color:var(--ss-panel-elevated)] disabled:opacity-50"
        >
          {isPending ? "Instantiating…" : "Instantiate"}
        </button>
        {status === "ok" && (
          <span className="font-mono text-[0.48rem] uppercase tracking-widest text-emerald-400">
            Rule added (draft)
          </span>
        )}
        {status === "error" && errorMsg && (
          <span className="font-mono text-[0.48rem] uppercase tracking-widest text-orange-400">
            {errorMsg}
          </span>
        )}
      </div>
    </div>
  );
}
