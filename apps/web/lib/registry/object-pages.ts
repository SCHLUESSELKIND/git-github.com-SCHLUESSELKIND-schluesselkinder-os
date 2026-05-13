import { getObjectByCode, getPublicObjects, getPublicReleaseSignals } from "../../../../packages/registry/src/index";

type MetadataRow = readonly [label: string, value: string];

type StaticObjectArchiveRecord = Readonly<{
  archiveClass: string;
  board: Readonly<{
    alt: string;
    height: number;
    src: string;
    width: number;
  }>;
  id: string;
  metadata: readonly MetadataRow[];
  status: string;
  surface: string;
  title: string;
  transaction: string;
  year: string;
}>;

type StaticShopObject = Readonly<{
  archiveClass: string;
  boardSrc: string;
  href: string;
  id: string;
  objectClass: string;
  releaseCode: string | null;
  state: string;
  title: string;
}>;

type StaticShopProjection = Readonly<{
  objects: readonly StaticShopObject[];
  releaseCodes: readonly string[];
}>;

const objectPresentation = {
  "SK-001": {
    archiveClass: "SK-CORE",
    board: {
      alt: "SCHLUESSELKINDER SK-001 BLACK HOODIE / KEY institutional archive board",
      height: 1122,
      src: "/objects/sk-001/archive-board.png",
      width: 1402
    },
    mark: "KEY",
    status: "SEALED",
    surface: "BLACK-ON-BLACK",
    transaction: "CLOSED",
    year: "2026"
  },
  "SK-002": {
    archiveClass: "SK-ARTIFACT",
    board: {
      alt: "SCHLUESSELKINDER SK-002 SHIBARI KAWAII ROPEMASTER HOODIE institutional archive board",
      height: 1024,
      src: "/objects/sk-002/archive-board.png",
      width: 1536
    },
    mark: "ROPEMASTER",
    status: "ACTIVE ARCHIVE",
    surface: "BLACK-ON-BLACK",
    transaction: "CLOSED",
    year: "2026"
  }
} as const;

type PublicObjectCode = keyof typeof objectPresentation;

function getObjectPresentation(objectCode: string) {
  if (!(objectCode in objectPresentation)) {
    throw new Error(`Public object presentation not found for ${objectCode}.`);
  }

  return objectPresentation[objectCode as PublicObjectCode];
}

function getReleaseCodeForKey(releaseKey: string | null): string | null {
  if (!releaseKey) {
    return null;
  }

  return getPublicReleaseSignals().find((release) => release.releaseKey === releaseKey)?.releaseCode ?? null;
}

function formatNullableReference(reference: string | null) {
  return reference ?? "NONE";
}

export function getStaticObjectArchiveRecord(objectCode: PublicObjectCode): StaticObjectArchiveRecord {
  const object = getObjectByCode(objectCode);

  if (!object) {
    throw new Error(`Public object projection not found for ${objectCode}.`);
  }

  const presentation = getObjectPresentation(objectCode);
  const releaseReference = getReleaseCodeForKey(object.releaseKey);

  return {
    archiveClass: presentation.archiveClass,
    board: presentation.board,
    id: object.objectCode,
    metadata: [
      ["record", object.objectCode],
      ["object", object.title],
      ["object class", object.objectClass],
      ["mark", presentation.mark],
      ["surface", presentation.surface],
      ["status", presentation.status],
      ["transaction", presentation.transaction],
      ["release reference", formatNullableReference(releaseReference)],
      ["archive class", presentation.archiveClass],
      ["year", presentation.year]
    ],
    status: presentation.status,
    surface: presentation.surface,
    title: object.title,
    transaction: presentation.transaction,
    year: presentation.year
  };
}

export function getStaticShopProjection(): StaticShopProjection {
  const releases = getPublicReleaseSignals();
  const releaseCodes = releases.map((release) => release.releaseCode);
  const objects = getPublicObjects().map((object) => {
    const presentation = getObjectPresentation(object.objectCode);
    const releaseCode = object.releaseKey
      ? releases.find((release) => release.releaseKey === object.releaseKey)?.releaseCode ?? null
      : null;

    return {
      archiveClass: presentation.archiveClass,
      boardSrc: presentation.board.src,
      href: `/objects/${object.objectCode.toLowerCase()}`,
      id: object.objectCode,
      objectClass: object.objectClass,
      releaseCode,
      state: presentation.status,
      title: object.title
    };
  });

  return {
    objects,
    releaseCodes
  };
}
