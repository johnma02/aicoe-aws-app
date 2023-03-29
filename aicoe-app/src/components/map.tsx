import { GoogleMap, LoadScript, GroundOverlay, Circle } from '@react-google-maps/api';
import styles from '@/styles/Home.module.css';
import {useState, useEffect} from 'react';  
import Image from 'next/image';

interface MapProps {
  latitude: number;
  longitude: number;
  zoom: number;
}

export default function Map({latitude, longitude, zoom}: MapProps): JSX.Element {
    const [loaded, setLoaded] = useState<boolean>(false);
    const [overlayLoaded, setOverlayLoaded] = useState<boolean>(false);
    const [riskPredictions, setRiskPredictions] = useState<string>("/test_images/Event0_projected.png");
    const mapCenter = {
        lat: latitude,
        lng: longitude
    };

    const containerStyle = {
        width: '700px',
        height: '700px'
    };

    const bounds = {
        north: 57.150000,
        south: 30.712216,
        east: -64.52544,
        west: -103.118009,
    };
 
    useEffect(()=> {
        console.log("triggered re-render");

    } ,[loaded]);
    
    useEffect(()=>{
        if(overlayLoaded){
            console.log("components mounted: triggered re-render");
            setLoaded(false); // Not sure why this works.
        }
    }, [overlayLoaded]);

    return (
        <div className={styles.box}>
            <LoadScript
                googleMapsApiKey={process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY as string}
                onLoad={() => console.log('LoadScript Ready!')}
                onError={() => console.log('Google Maps script loading failed')}
            >
                <GoogleMap
                    id="runoff-risk-map"
                    zoom={zoom}
                    center={mapCenter}
                    mapContainerStyle={containerStyle}
                    onLoad={() => setLoaded(true)}
                >
                    {loaded && <div>
                        <GroundOverlay
                            url={riskPredictions}
                            bounds={bounds}
                            onLoad={()=>setOverlayLoaded(true)}
                            opacity={.5}
                        />
                    </div>}
                </GoogleMap>
            </LoadScript>
        </div>
    );
}
