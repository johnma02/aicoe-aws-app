import { GoogleMap, LoadScript, GroundOverlay } from '@react-google-maps/api';
import styles from '@/styles/Home.module.css';
import {useState, useEffect} from 'react';  
import AWS from 'aws-sdk';

interface MapProps {
  latitude: number;
  longitude: number;
  zoom: number;
}

export default function Map({latitude, longitude, zoom}: MapProps): JSX.Element {
    const [loaded, setLoaded] = useState<boolean>(false);
    const [day, setDay] = useState<number>(0);
    const [imageUrl, setImageUrl] = useState<string>("");
    const [imageLoaded, setImageLoaded] = useState<boolean>(false);
    
    const mapCenter = {
        lat: latitude,
        lng: longitude
    };

    const containerStyle = {
        width: '675px',
        height: '675px'
    };

    const bounds = {
        north: 57.05,
        south: 30.85,
        east: -65.5,
        west: -102.4,
    };
    
    useEffect(() => {
        if(loaded){
            const s3 = new AWS.S3({
                region: process.env.NEXT_PUBLIC_AWS_REGION as string,
                accessKeyId: process.env.NEXT_PUBLIC_ACCESS_KEY_ID as string,
                secretAccessKey: process.env.NEXT_PUBLIC_SECRET_ACCESS_KEY as string
            });
        
            const params = {
                Bucket: process.env.NEXT_PUBLIC_S3_BUCKET as string,
                Key: "day"+day.toString()+".png",
            };

            s3.getObject(params, (err: AWS.AWSError, data: AWS.S3.GetObjectOutput) => {
                if (err) {
                    console.error(err);
                    return;
                }

                const objectUrl = URL.createObjectURL(new Blob([data.Body as string]));
                setImageUrl(objectUrl);
                setImageLoaded(true);
                console.log("image loaded");
            });
        }
    }, [day, loaded]);

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
                    {(loaded && imageLoaded) && <div>
                        <GroundOverlay
                            url={imageUrl}
                            bounds={bounds}
                            opacity={.3}
                        />
                    </div>}
                </GoogleMap>
            </LoadScript>
        </div>
    );
}
