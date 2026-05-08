import { BrandSymbol } from "./BrandSymbol";

type EditorialImageProps = Readonly<{
  alt: string;
  caption?: string;
  className?: string;
  imageClassName?: string;
  priority?: boolean;
  src: string;
  symbol?: "key" | "horn" | "ropeface" | "none";
}>;

export function EditorialImage({ alt, caption, className = "", imageClassName = "", priority = false, src, symbol = "key" }: EditorialImageProps) {
  return (
    <figure className={`relative overflow-hidden border border-stone-800 bg-black ${className}`}>
      <img
        alt={alt}
        className={`h-full w-full object-cover ${imageClassName}`}
        decoding={priority ? "sync" : "async"}
        loading={priority ? "eager" : "lazy"}
        src={src}
      />
      <div className="pointer-events-none absolute inset-0 bg-black/25 mix-blend-multiply" />
      {symbol !== "none" ? (
        <div className="absolute bottom-5 left-5 text-stone-100/80">
          <BrandSymbol className="h-14 w-14" variant={symbol} />
        </div>
      ) : null}
      {caption ? (
        <figcaption className="absolute right-5 top-5 max-w-48 text-right text-xs font-black uppercase text-stone-100">
          {caption}
        </figcaption>
      ) : null}
    </figure>
  );
}
