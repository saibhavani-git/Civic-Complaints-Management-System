"use client";

import { useEffect, useId, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export interface HeatPoint {
  lat: number;
  lng: number;
  weight: number;
}

function HeatmapMap({ points, mapKey }: { points: HeatPoint[]; mapKey: string }) {
  const center: [number, number] =
    points.length > 0 ? [points[0].lat, points[0].lng] : [28.6139, 77.209];

  return (
    <MapContainer key={mapKey} center={center} zoom={12} className="h-full w-full">
      <TileLayer
        attribution="&copy; OpenStreetMap"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {points.map((p, i) => (
        <CircleMarker
          key={`${p.lat}-${p.lng}-${i}`}
          center={[p.lat, p.lng]}
          radius={Math.min(24, 6 + p.weight * 2)}
          pathOptions={{ color: "#dc2626", fillColor: "#ef4444", fillOpacity: 0.45 }}
        >
          <Popup>{p.weight} complaint(s)</Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}

export function ComplaintHeatmap({ points }: { points: HeatPoint[] }) {
  const reactId = useId();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  if (!mounted) {
    return <div className="h-80 w-full rounded-xl border bg-muted/30 animate-pulse" aria-hidden />;
  }

  return (
    <div className="h-80 w-full overflow-hidden rounded-xl border">
      <HeatmapMap mapKey={`heatmap-${reactId}`} points={points} />
    </div>
  );
}
