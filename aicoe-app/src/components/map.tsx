import { GoogleMap, useLoadScript } from '@react-google-maps/api';
import { useMemo } from 'react';
import styles from '@/styles/Home.module.css';

interface MapProps{
    lattitude: number;
    longitude: number;
    zoom: number;
}

export default function Map({lattitude, longitude, zoom}: MapProps):JSX.Element {
    const mapCenter = useMemo(
        () => ({ lat:lattitude, lng: longitude }),
        []
    );
    const mapOptions = useMemo<google.maps.MapOptions>(
        () => ({
            clickableIcons: true,
        }),
        []
    );
    const { isLoaded } = useLoadScript({
        googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY as string,
    });
    if (!isLoaded) {
        return <div>Google Maps is loading...</div>;
    }
    console.log("FINDING: "+JSON.stringify(process.env));
    return (
        <div className={styles.homeWrapper}>
            <div className={styles.sidebar}>
            </div>
            <GoogleMap
                options={mapOptions}
                zoom={zoom}
                center={mapCenter}
                mapTypeId={google.maps.MapTypeId.ROADMAP}
                mapContainerStyle={{ width: '800px', height: '800px' }}
                onLoad={() => console.log('Google Maps component loaded')}
            />
        </div>
    );
}