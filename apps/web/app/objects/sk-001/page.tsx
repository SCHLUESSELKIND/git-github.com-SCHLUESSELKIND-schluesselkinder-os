import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { ObjectArchiveRecordView } from "../_components/ObjectArchiveRecordView";
import { getStaticObjectArchiveRecord } from "../../../lib/registry/object-pages";

const description = "Archive record for SK-001 BLACK HOODIE / KEY.";
const image = "/objects/sk-001/archive-board.png";
const title = `SK-001 BLACK HOODIE / KEY | ${masterbrand}`;

export const metadata: Metadata = {
  alternates: {
    canonical: "/objects/sk-001"
  },
  description,
  openGraph: {
    description,
    images: [{ alt: "SK-001 BLACK HOODIE / KEY archive board", height: 1122, url: image, width: 1402 }],
    title,
    url: "/objects/sk-001"
  },
  title,
  twitter: {
    card: "summary_large_image",
    description,
    images: [image],
    title
  }
};

export default function Sk001Page() {
  const record = getStaticObjectArchiveRecord("SK-001");

  return <ObjectArchiveRecordView record={record} />;
}
