import { brandAssets } from "@schluesselkinder/brand";

type BrandSymbolProps = Readonly<{
  className?: string;
  label?: string;
  variant?: "key" | "horn" | "ropeface";
}>;

export function BrandSymbol({ className = "", label = "SCHLUESSELKINDER symbol", variant = "key" }: BrandSymbolProps) {
  if (variant === "ropeface") {
    return (
      <img
        alt={label}
        className={`object-contain ${className}`}
        src={brandAssets.shibariKawaiiRopeface}
      />
    );
  }

  if (variant === "horn") {
    return (
      <svg aria-label={label} className={className} role="img" viewBox="0 0 120 120">
        <path d="M31 17C16 37 17 59 36 76C41 68 47 61 53 57C42 47 35 34 31 17Z" fill="currentColor" />
        <path d="M89 17C104 37 103 59 84 76C79 68 73 61 67 57C78 47 85 34 89 17Z" fill="currentColor" />
        <path d="M38 84C48 90 55 94 60 103C65 94 72 90 82 84C72 82 66 80 60 74C54 80 48 82 38 84Z" fill="currentColor" />
      </svg>
    );
  }

  return (
    <img
      alt={label}
      className={`object-contain ${className}`}
      src={brandAssets.runeKeyMark}
    />
  );
}
