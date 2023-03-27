import { GoogleMap, useLoadScript, OverlayView } from '@react-google-maps/api';
import styles from '@/styles/Home.module.css';
import Image from 'next/image';

interface MapProps{
    latitude: number;
    longitude: number;
    zoom: number;
}


// TODO: Overlay using Google Maps API 

export default function Map({latitude, longitude, zoom}: MapProps):JSX.Element {
    const mapCenter = {
        lat: latitude,
        lng: longitude
    };
   
    const containerStyle = {
        width: '700px',
        height: '700px'
    };
    const { isLoaded } = useLoadScript({
        googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY as string,
    });
    
    if (!isLoaded) {
        return <div>Google Maps is loading...</div>;
    }
    return (
        <div className={styles.homeWrapper}>
            <GoogleMap
                id="runoff-risk-map"
                zoom={zoom}
                center={mapCenter}
                mapTypeId={google.maps.MapTypeId.ROADMAP}
                mapContainerStyle={containerStyle}
                onLoad={() => console.log('Google Maps component loaded')}
            >
                <OverlayView 
                    position={mapCenter} 
                    mapPaneName={OverlayView.OVERLAY_LAYER}
                    onLoad={()=>console.log("Overlay loaded")}
                >
                    <div className={styles.header}>                    
                    hello test!
                        <Image
                            src='/test_images/Event0_projected.png' alt='projection' fill/> 
                    </div>

                </OverlayView>
            
            </GoogleMap>
        </div>
    );
}