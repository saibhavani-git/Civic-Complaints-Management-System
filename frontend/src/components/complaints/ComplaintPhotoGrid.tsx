"use client";

export function ComplaintPhotoGrid({
  images,
  altPrefix,
}: {
  images: { url: string }[];
  altPrefix: string;
}) {
  if (!images?.length) return null;

  return (
    <div className="flex gap-3 flex-wrap">
      {images.map((img, i) => (
        <a
          key={`${img.url}-${i}`}
          href={img.url}
          target="_blank"
          rel="noopener noreferrer"
          className="block"
        >
          <img
            src={img.url}
            alt={`${altPrefix} ${i + 1}`}
            className="h-32 w-32 rounded-lg object-cover border hover:opacity-90 transition-opacity"
          />
        </a>
      ))}
    </div>
  );
}
