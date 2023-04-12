import styles from '@/styles/Home.module.css';
import { Box, Tab, TabList, TabPanel, TabPanels, Tabs } from '@chakra-ui/react';

interface SlidebarProps{
    day: number;
    setDay: (day: number) => void;
}

export default function Slidebar({day, setDay}: SlidebarProps):JSX.Element{
    function handleSliderChange(event: React.ChangeEvent<HTMLInputElement>){
        setDay(parseInt(event.target.value, 10));
    };

    function handleTabsChange(index: number) {
        setDay(index);
    };

    return (
        <Box>
            <input
                type='range'
                min='0'
                max='2'
                value={day}
                onChange={(event) => handleSliderChange(event)}
            />

            <Tabs index={day} onChange={(index: number) => handleTabsChange(index)}>
                <TabList>
                    <Tab>One</Tab>
                    <Tab>Two</Tab>
                    <Tab>Three</Tab>
                </TabList>
                <TabPanels>
                    <TabPanel>
                        <p>Click the tabs or pull the slider around</p>
                    </TabPanel>
                    <TabPanel>
                        <p>Yeah yeah. Whats up?</p>
                    </TabPanel>
                    <TabPanel>
                        <p>Oh, hello there.</p>
                    </TabPanel>
                </TabPanels>
            </Tabs>
        </Box>
    );
}