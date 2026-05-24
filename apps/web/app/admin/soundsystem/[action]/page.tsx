import { notFound, redirect } from "next/navigation";
import { AwaitingWire } from "../_components/AwaitingWire";
import { COMMAND_INTENTS } from "../_lib/operators";

type ActionPageProps = Readonly<{
  params: Promise<{ action: string }>;
}>;

export function generateStaticParams() {
  return COMMAND_INTENTS.filter((intent) => intent.targetPath === undefined).map(
    (intent) => ({ action: intent.slug })
  );
}

export default async function SoundsystemActionPage({ params }: ActionPageProps) {
  const { action } = await params;
  const intent = COMMAND_INTENTS.find((entry) => entry.slug === action);

  if (!intent) {
    notFound();
  }

  if (intent.targetPath !== undefined) {
    redirect(intent.targetPath);
  }

  return <AwaitingWire intent={intent} />;
}
