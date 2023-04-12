import styles from '@/styles/Home.module.css';
import { Card, SliderFilledTrack, SliderThumb, SliderTrack } from '@chakra-ui/react';
import {Tab, TabList, TabPanel, TabPanels, Tabs} from '@chakra-ui/react';
import {Slider} from '@chakra-ui/react';
interface SlidebarProps{
    day: number;
    setDay: (day: number) => void;
}

export default function Slidebar({day, setDay}: SlidebarProps):JSX.Element{
    function handleSliderChange(event: number){
        setDay(event);
    };

    function handleTabsChange(index: number) {
        setDay(index);
    };

    return (
        <Card variant="elevated" paddingLeft="20px" paddingRight="20px">
            <Slider
                width="100%"
                value={day}
                min={0}
                max={9}
                onChange={(event) => handleSliderChange(event)}>
                <SliderTrack>
                    <SliderFilledTrack />
                </SliderTrack>
                <SliderThumb />
            </Slider>

            <Tabs index={day} onChange={(index: number) => handleTabsChange(index)} isFitted={true}>
                <TabList>
                    {[...Array(10).keys()].map((x)=>(
                        <Tab key={x}> {x+1}</Tab>
                    ))}
                </TabList>
            </Tabs>
        </Card>
    );
}