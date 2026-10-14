"use client";

import { useEffect, useId, useState } from "react";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const icon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

function PinHandler({ onChange }: { onChange: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onChange(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

/** Pan map when coordinates change from GPS / form (not on every minor update). */
function MapRecenter({ latitude, longitude }: { latitude: number; longitude: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView([latitude, longitude], map.getZoom(), { animate: true });
  }, [latitude, longitude, map]);
  return null;
}

function LocationMap({
  latitude,
  longitude,
  onChange,
  mapKey,
}: {
  latitude: number;
  longitude: number;
  onChange: (lat: number, lng: number) => void;
  mapKey: string;
}) {
  return (
    <MapContainer
      key={mapKey}
      center={[latitude, longitude]}
      zoom={14}
      scrollWheelZoom
      className="h-full w-full"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapRecenter latitude={latitude} longitude={longitude} />
      <Marker
        position={[latitude, longitude]}
        icon={icon}
        draggable
        eventHandlers={{
          dragend: (e) => {
            const { lat, lng } = e.target.getLatLng();
            onChange(lat, lng);
          },
        }}
      />
      <PinHandler onChange={onChange} />
    </MapContainer>
  );
}

export function LocationPicker({
  latitude,
  longitude,
  onChange,
}: {
  latitude: number;
  longitude: number;
  onChange: (lat: number, lng: number) => void;
}) {
  const reactId = useId();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  if (!mounted) {
    return <div className="h-56 w-full rounded-lg border bg-muted/30 animate-pulse" aria-hidden />;
  }

  return (
    <div className="h-56 w-full overflow-hidden rounded-lg border">
      <LocationMap
        mapKey={`location-picker-${reactId}`}
        latitude={latitude}
        longitude={longitude}
        onChange={onChange}
      />
    </div>
  );
}
