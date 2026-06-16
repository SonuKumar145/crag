import React, { useState, useEffect, useRef } from 'react';
import { Text, Box, useStdout } from 'ink';
import { spawn, ChildProcessWithoutNullStreams } from 'child_process';
import path from "path";
import TextInput from 'ink-text-input';
import readline from 'readline';
import Spinner from './spinner.js';
import gradient from 'gradient-string'

const ENTER_ALT_SCREEN = '\x1b[?1049h';
const LEAVE_ALT_SCREEN = '\x1b[?1049l';

const status_color = {
	'ok': 'green',
	'inprocess': 'white',
	'done': 'green',
	'warning': 'yellow',
	'error': 'red',
}

export default function App() {
	const [input, setInput] = useState('');
	const [history, setHistory] = useState<string[]>(['Bot: Hello! How can I help you today?']);
	const [isTyping, setIsTyping] = useState(false);
	const { stdout } = useStdout();
	const [agentReady, setAgentReady] = useState(false);
	const [setupMessages, setSetupMessages] = useState<Record<string, {
		message: string,
		status: "inprocess" | "done" | "error" | "ok" | "warning"
	}>>({});

	const [size, setSize] = useState({
		columns: stdout.columns || 80,
		rows: stdout.rows || 24,
	});

	useEffect(() => {
		const handleResize = () => {
			setSize({
				columns: stdout.columns || 80,
				rows: stdout.rows || 24,
			});
		};

		stdout.on('resize', handleResize);
		return () => {
			stdout.off('resize', handleResize);
		};
	}, [stdout]);

	// Keep a persistent reference to the background Python process
	const pyProcess = useRef<ChildProcessWithoutNullStreams | null>(null);

	useEffect(() => {
		pyProcess.current = spawn(path.join(process.cwd(), '.venv', 'bin', 'python'), ['-u', 'agent.py']);

		const rl = readline.createInterface({
			input: pyProcess.current.stdout,
			terminal: false
		});

		rl.on('line', (line) => {
			try {
				const response = JSON.parse(line.trim());

				setSetupMessages(prev => ({ ...prev, [response.id]: response }));

				if (response.status === "ok" && response.id === "agent_ready") {
					setAgentReady(true);
				}
			} catch (err) {
				setHistory(prev => [...prev, `Raw Output: ${line}`]);
			}
			setIsTyping(false);
		});

		pyProcess.current.stderr.on('data', (data) => {
			setSetupMessages(prev => ({
				...prev,
				"py_crash": { message: `PYTHON ERROR: ${data.toString()}`, status: "error" }
			}));
		});

		// FIX 3: Catch Spawn Errors (e.g., ENOENT missing virtual env)
		pyProcess.current.on('error', (err) => {
			setSetupMessages(prev => ({
				...prev,
				"sys_error": { message: `SPAWN ERROR: ${err.message}`, status: "error" }
			}));
		});

		// FIX 4: Catch Premature Exits
		pyProcess.current.on('close', (code) => {
			if (code !== 0) {
				setSetupMessages(prev => ({
					...prev,
					"sys_close": { message: `Process exited with code ${code}`, status: "error" }
				}));
			}
		});

		return () => {
			pyProcess.current?.kill();
		};
	}, []);

	const handleSubmit = (value: string) => {
		if (!value.trim() || isTyping) return;

		setHistory(prev => [...prev, `You: ${value}`]);
		setIsTyping(true);
		setInput('');

		const payload = JSON.stringify({ message: value });
		pyProcess.current?.stdin.write(payload + '\n');
	};

	return (
		<Box
			flexDirection="column"
			padding={1}
			width={size.columns}
			height={size.rows}
			borderStyle="single"
			borderColor="dim"
		>
			<Box marginBottom={3} flexDirection='column'>
				<Text color="magenta">
					{gradient(['#3b82f6', '#8b5cf6'])('█▀▀ █▀█ ▄▀█ █▀▀ █▀▀ █▄░█ ▀█▀')}
				</Text>
				<Text color="magenta">
					{gradient(['#3b82f6', '#8b5cf6'])('█▄▄ █▀▄ █▀█ █▄█ ██▄ █░▀█ ░█░')}
				</Text>
				<Text>{'─'.repeat(size.columns-4)}</Text>
				<Text>{'─'.repeat(size.columns-4)}</Text>
			</Box>
			{
				!agentReady ? (
					<Box flexDirection='row'>
						<Text color="whiteBright">
							Initialising
						</Text>
						<Spinner color="whiteBright" />
					</Box>
				) : null
			}
			<Box flexDirection='column' justifyContent="space-between" flexGrow={1}>
				{
					agentReady ? (
						<Box flexDirection="column" marginBottom={1}>
							{history.map((msg, index) => (
								<Box>
									<Text key={index} color={msg.startsWith('You:') ? 'green' : 'white'}>
										{msg}
									</Text>
									{/* {
								msg
							} */}
								</Box>
							))}
							{isTyping && <Text color="yellow" dimColor>Bot is thinking...</Text>}
						</Box>
					) : (
						<Box flexDirection="column"
							borderStyle="single"
							borderColor="dim">
							{Object.entries(setupMessages).map(([id, msgDetails]) => (
								<Box flexDirection="row">
									<Text key={id} color={status_color[msgDetails.status]}>
										{msgDetails.message}
									</Text>
									{
										msgDetails.status == "inprocess" ? (
											<Spinner color={status_color['inprocess']} />
										) : null
									}
								</Box>

							))}
						</Box>
					)
				}
				{
					agentReady ? (
						<Box>
							<Text bold color="cyan">➔ </Text>
							<TextInput
								value={input}
								onChange={setInput}
								onSubmit={handleSubmit}
								placeholder="Type a message and press Enter..."
							/>
						</Box>
					) : null
				}
			</Box>
		</Box>
	);
}

process.stdout.write(ENTER_ALT_SCREEN);

process.on('exit', () => {
	process.stdout.write(LEAVE_ALT_SCREEN);
});