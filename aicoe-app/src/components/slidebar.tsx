import styles from '@/styles/Home.module.css';

interface SlidebarProps{
    day: number;
    setDay: (day: number) => void;
}

export default function Slidebar({day, setDay}: SlidebarProps):JSX.Element{
    return (
        <div className={styles.box} style={{textAlign:"left"}}>
            <h3>Forecast (Daily)</h3>
            <div className={styles.gridten}>
                {[...Array(10).keys()].map((x: number)=>(
                    <div 
                        className={styles.card} 
                        key={x} 
                        onClick={()=> setDay(x)}
                        style={{backgroundColor: x === day ? "lightblue" : "transparent"}}
                    >
                        {x+1}
                    </div>
                ))}
            </div> 
        </div>
    );
}