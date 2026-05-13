import type { Metadata } from "next";
import { ObjectArchiveRecordView } from "../_components/ObjectArchiveRecordView";
import { getStaticObjectArchiveRecord } from "../../../lib/registry/object-pages";

const collectiveName = "SCHLUESSELKINDER";

export const metadata: Metadata = {
  title: `SK-001 BLACK HOODIE / KEY | ${collectiveName}`,
  description: "SCHLUESSELKINDER object archive record SK-001."
};

export default function Sk001Page() {
  const record = getStaticObjectArchiveRecord("SK-001");

  return <ObjectArchiveRecordView record={record} />;
}
