import { notFound } from "next/navigation";
import { AwaitingWire } from "../_components/AwaitingWire";
import { COMMAND_INTENTS } from "../_lib/operators";

type ActionPageProps = Readonly<{
  params: Promise<{ action: string }>;
}>;

export function generateStaticParams() {
  return COMMAND_INTENTS.map((intent) => ({ action: intent.slug }));
}

export default async function SoundsystemActionPage({ params }: ActionPageProps) {
  const { action } = await params;
  const intent = COMMAND_INTENTS.find((entry) => entry.slug === action);

  if (!intent) {
    notFound();
  }

  return <AwaitingWire intent={intent} />;
}
