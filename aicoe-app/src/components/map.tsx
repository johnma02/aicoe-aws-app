import { GoogleMap, LoadScript, GroundOverlay } from '@react-google-maps/api';
import styles from '@/styles/Home.module.css';
import {useState, useEffect, useRef} from 'react';  
import AWS from 'aws-sdk';
import Slidebar from '@/components/slidebar';

interface MapProps {
  latitude: number;
  longitude: number;
  zoom: number;
}

interface ImageCache {
    [key: number] : string;
}
export default function Map({latitude, longitude, zoom}: MapProps): JSX.Element {
    const [loaded, setLoaded] = useState<boolean>(false);
    const [day, setDay] = useState<number>(0);
    const [imageCache, setImageCache] = useState<ImageCache>({});
    const [imagesLoaded, setImagesLoaded] = useState<boolean>(false);

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
        
            const cache: ImageCache = [...Array(10).keys()]
                .reduce((accum: ImageCache, x: number)=>{
                    const params = {
                        Bucket: process.env.NEXT_PUBLIC_S3_BUCKET as string,
                        Key: "day"+x.toString()+".png",
                    };

                    s3.getObject(params, (err: AWS.AWSError, data: AWS.S3.GetObjectOutput) => {
                        if (err) {
                            console.error(err);
                            return;
                        }
            
                        const objectUrl = URL.createObjectURL(new Blob([data.Body as string]));
                        setImageCache(prevState => ({...prevState, [x]: objectUrl}));
                    });
                    return accum;
                }, []);
        }
    }, [loaded]);
    
    useEffect(() => {
        if (Object.keys(imageCache).length === 10) {
            setImagesLoaded(true);
        }
    }, [imageCache]);

    return (
        <div>
            <div className={styles.box}>
                <LoadScript
                    googleMapsApiKey={process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY as string}
                    onLoad={() => console.log('LoadScript ready')}
                    onError={() => console.log('Google Maps script loading failed')}
                >
                    <GoogleMap
                        id="runoff-risk-map"
                        zoom={zoom}
                        center={mapCenter}
                        mapContainerStyle={containerStyle}
                        onLoad={() => setLoaded(true)}
                    >
                        {(loaded && imagesLoaded) && 
                            <GroundOverlay
                                url={imageCache[day]}
                                key={day}
                                bounds={bounds}
                                opacity={.3}
                                onUnmount={(groundOverlay)=> {
                                    const mapDiv = groundOverlay.getMap()?.getDiv();
                                    const imgsToRemove = Array.from(mapDiv?.querySelectorAll('img[src*="blob"]') ?? []);

                                    imgsToRemove.forEach((node) => {
                                        node.remove();
                                    });
                                    groundOverlay.setMap(null);
                                    groundOverlay.setOpacity(0);
                                }}
                            />
                                
                        }
                    </GoogleMap>
                </LoadScript>
            </div>
            <Slidebar day={day} setDay={setDay}/>
        </div>
    );
}
