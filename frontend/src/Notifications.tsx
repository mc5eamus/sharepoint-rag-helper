import useWebSocket, { ReadyState } from 'react-use-websocket';
import { useState, useEffect } from "react";
import Snackbar from '@mui/material/Snackbar';

interface IntercomProps {
    socketUrl: string;
}

const Intercom: React.FC<IntercomProps> = ({ socketUrl }) => {

    const [state, setState] = useState({ open: false, message: '' });
    const { sendMessage, lastMessage, readyState } = useWebSocket(socketUrl);

    const connectionStatus = {
        [ReadyState.CONNECTING]: 'Connecting',
        [ReadyState.OPEN]: 'Open',
        [ReadyState.CLOSING]: 'Closing',
        [ReadyState.CLOSED]: 'Closed',
        [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
    }[readyState];
  
    useEffect(() => {
        setState({open: true, message: lastMessage?.data ?? ''})
    }, [lastMessage]);

    const handleClose = (event: React.SyntheticEvent | Event, reason?: string) => {
        if (reason === 'clickaway') {
          return;
        }
        setState({open: false, message: ''});
      };

    return ( <div>
        <Snackbar anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
            open={state.open && state.message !== ''} onClose={handleClose} 
            message={state.message} />
        </div>);
  }

export default Intercom;