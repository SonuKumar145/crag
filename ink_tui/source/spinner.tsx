
import React, { useState, useEffect } from 'react';
import { Text } from 'ink';

const Spinner = ({color}:{color:string}) => {
	const [frame, setFrame] = useState(0);
	const frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

	useEffect(() => {
		const timer = setInterval(() => {
			setFrame(prev => (prev + 1) % frames.length);
		}, 80);

		return () => clearInterval(timer);
	}, []);

	return <Text color={color}>{frames[frame]} </Text>;
};

export default Spinner