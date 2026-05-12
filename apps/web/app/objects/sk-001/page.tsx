import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { ObjectArchiveRecordView, type ObjectArchiveRecord } from "../_components/ObjectArchiveRecordView";

export const metadata: Metadata = {
  title: `SK-001 BLACK HOODIE / KEY | ${masterbrand}`,
  description: "SCHLUESSELKINDER object archive record SK-001."
};

const record: ObjectArchiveRecord = {
  archiveClass: "SK-CORE",
  board: {
    alt: "SCHLUESSELKINDER SK-001 BLACK HOODIE / KEY institutional archive board",
    height: 1122,
    src: "/objects/sk-001/archive-board.png",
    width: 1402
  },
  id: "SK-001",
  metadata: [
    ["record", "SK-001"],
    ["object", "BLACK HOODIE / KEY"],
    ["object type", "HOODIE"],
    ["mark", "KEY"],
    ["surface", "BLACK-ON-BLACK"],
    ["status", "SEALED"],
    ["transaction", "CLOSED"],
    ["archive class", "SK-CORE"],
    ["year", "2026"]
  ],
  status: "SEALED",
  surface: "BLACK-ON-BLACK",
  title: "BLACK HOODIE / KEY",
  transaction: "CLOSED",
  year: "2026"
};

export default function Sk001Page() {
  return <ObjectArchiveRecordView record={record} />;
}
