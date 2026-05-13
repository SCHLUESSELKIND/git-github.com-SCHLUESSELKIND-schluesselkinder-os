import type { Metadata } from "next";
import { ObjectArchiveRecordView } from "../_components/ObjectArchiveRecordView";
import { getStaticObjectArchiveRecord } from "../../../lib/registry/object-pages";

const collectiveName = "SCHLUESSELKINDER";

export const metadata: Metadata = {
  title: `SK-002 ROPEMASTER HOODIE | ${collectiveName}`,
  description: "SCHLUESSELKINDER object archive record SK-002."
};

export default function Sk002Page() {
  const record = getStaticObjectArchiveRecord("SK-002");

  return <ObjectArchiveRecordView record={record} />;
}
