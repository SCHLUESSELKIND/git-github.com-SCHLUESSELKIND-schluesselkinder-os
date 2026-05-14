import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { ObjectArchiveRecordView } from "../_components/ObjectArchiveRecordView";
import { getStaticObjectArchiveRecord } from "../../../lib/registry/object-pages";

const description = "Archive record for SK-002 SHIBARI KAWAII ROPEMASTER HOODIE.";
const image = "/objects/sk-002/archive-board.png";
const title = `SK-002 ROPEMASTER HOODIE | ${masterbrand}`;

export const metadata: Metadata = {
  alternates: {
    canonical: "/objects/sk-002"
  },
  description,
  openGraph: {
    description,
    images: [{ alt: "SK-002 SHIBARI KAWAII ROPEMASTER HOODIE archive board", height: 1024, url: image, width: 1536 }],
    title,
    url: "/objects/sk-002"
  },
  title,
  twitter: {
    card: "summary_large_image",
    description,
    images: [image],
    title
  }
};

export default function Sk002Page() {
  const record = getStaticObjectArchiveRecord("SK-002");

  return <ObjectArchiveRecordView record={record} />;
}
