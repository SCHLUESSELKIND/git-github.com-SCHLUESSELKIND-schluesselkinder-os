import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { ObjectArchiveRecordView, type ObjectArchiveRecord } from "../_components/ObjectArchiveRecordView";

export const metadata: Metadata = {
  title: `SK-002 ROPEMASTER HOODIE | ${masterbrand}`,
  description: "SCHLUESSELKINDER object archive record SK-002."
};

const record: ObjectArchiveRecord = {
  archiveClass: "SK-ARTIFACT",
  board: {
    alt: "SCHLUESSELKINDER SK-002 SHIBARI KAWAII ROPEMASTER HOODIE institutional archive board",
    height: 1024,
    src: "/objects/sk-002/archive-board.png",
    width: 1536
  },
  id: "SK-002",
  metadata: [
    ["record", "SK-002"],
    ["object", "SHIBARI KAWAII ROPEMASTER HOODIE"],
    ["object type", "HOODIE"],
    ["mark", "ARTIST MARK"],
    ["surface", "BLACK-ON-BLACK"],
    ["status", "ACTIVE ARCHIVE"],
    ["transaction", "CLOSED"],
    ["archive class", "SK-ARTIFACT"],
    ["year", "2026"]
  ],
  status: "ACTIVE ARCHIVE",
  surface: "BLACK-ON-BLACK",
  title: "ROPEMASTER HOODIE",
  transaction: "CLOSED",
  year: "2026"
};

export default function Sk002Page() {
  return <ObjectArchiveRecordView record={record} />;
}
