import { GoogleMap, LoadScript, GroundOverlayF } from '@react-google-maps/api';
import styles from '@/styles/Home.module.css';
import {useState, useEffect} from 'react';  
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
        <div style={{width: "100%", height: "100%"}}>
            <LoadScript
                googleMapsApiKey={process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY as string}
                onLoad={() => console.log('LoadScript ready')}
                onError={() => console.log('Google Maps script loading failed')}
            >
                <GoogleMap
                    id="runoff-risk-map"
                    zoom={zoom}
                    center={mapCenter}
                    onLoad={() => setLoaded(true)}
                    mapContainerStyle={{width: "100%", height: "100%"}}
                >
                    {(loaded && imagesLoaded) && 
                            <GroundOverlayF
                                url={imageCache[day]}
                                bounds={bounds}
                                options={{opacity:.4}}
                            />
                    }
                </GoogleMap>
            </LoadScript>
            {/* <Slidebar day={day} setDay={setDay}/> */}
        </div>
    );
}
