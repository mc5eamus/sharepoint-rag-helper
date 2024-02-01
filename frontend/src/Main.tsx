import { useState } from "react";
import { useMsal } from "@azure/msal-react";
import { apiRequest, apiConfig } from "./config";
import { useEffect } from "react";
import axios from 'axios';

import { Box, TextField, Slider, Typography, Modal, AppBar, Toolbar, IconButton, CssBaseline, Drawer } from '@mui/material';
import LoadingButton from '@mui/lab/LoadingButton';

import SendIcon from '@mui/icons-material/Send';
import MenuIcon from '@mui/icons-material/Menu';

import Intercom from "./Notifications";
import ResultGrid from "./ResultGrid";

const modalStyle = {
    position: 'absolute' as 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 600,
    bgcolor: 'background.paper',
    border: '2px solid #000',
    boxShadow: 24,
    p: 4,
};

const marks = [
    { value: 1, label: '1', }, { value: 5, label: '5'}
  ];

const Main = () => {

    const saved_keywords = window.sessionStorage.getItem('app_keywords');
    const saved_query = window.sessionStorage.getItem('app_query');

    const [searchState, setSearchState] = useState({ 
        keywords: saved_keywords ?? '', 
        query: saved_query ?? '', 
        max_results: 3, 
        results: [], 
        loading: false});

    const [lightbox, setLightbox] = useState({ open: false, image: '' });
    const [socketUrl, setSocketUrl] = useState('')

    const [completions, setCompletions] = useState({open: false, content: ''});

    const { instance, inProgress } = useMsal();

    const getAccessToken = async () => {
        const account = instance.getActiveAccount();
        if (!account) {
            throw Error(
                "No active account! Verify a user has been signed in and setActiveAccount has been called."
            );
        }

        const tokenResponse = await instance.acquireTokenSilent({
            ...apiRequest,
            account: account
        });

        return tokenResponse.accessToken;
    }

    const bootstrap = async () => {
        const accessToken = await getAccessToken();
        axios.post(apiConfig.baseUri+ '/comms/negotiate',
        null,
        {
            headers: { Authorization: `Bearer ${accessToken}` }
        }).then(response => {
            setSocketUrl(response.data.url);
        });    
    }

    const callApi = async (allowIndexing:boolean) => {

        window.sessionStorage.setItem('app_keywords', searchState.keywords);
        window.sessionStorage.setItem('app_query', searchState.query);

        setSearchState({...searchState, loading: true});
    
        const accessToken = await getAccessToken();

        const url = apiConfig.baseUri+ (allowIndexing ? '/suggestions' : '/indexed');
        const response = await axios.post(url, 
            {
                query: searchState.query,
                keywords: searchState.keywords,
                max_results: searchState.max_results
            }, 
            {
                headers: { Authorization: `Bearer ${accessToken}` }
            });
        
        setSearchState({...searchState, results: response.data, loading: false});
    }

    const lightboxOpened = (item: any) => setLightbox({ open: true, image: apiConfig.baseUri+ "/media/" + item.snapshot })
    const lightboxClosed = () => setLightbox({open: false, image: ''});

    const openCompletionsResult = (content: string) => setCompletions({open: true, content: content});
    const completionsResultClosed = () => setCompletions({open: false, content: ''});

    const openInNewTab = (url:string) => {
        window.open(url, '_blank', 'noreferrer');
    };

    const queryResult = async (item: any) => {

        const accessToken = await getAccessToken();
        const response = await axios.post(apiConfig.baseUri+ '/completions/chat', 
            {
                query: searchState.query,
                text: item.content,
                image: item.snapshot
            }, 
            {
                headers: { Authorization: `Bearer ${accessToken}` }
            });
        response.data && openCompletionsResult(response.data);
    }
    
    useEffect(() => {
        if(socketUrl === '') {
            bootstrap();
        }
    }, [socketUrl]);

    
    return ( <Box sx={{ display:'flex'}}>
            <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
                <Toolbar>
                <IconButton size="small" edge="start" color="inherit" aria-label="open drawer" sx={{ mr: 2 }} >
                    <MenuIcon />
                </IconButton>
                <Typography variant="body1" noWrap component="div">SharePoint RAG Helper</Typography>
                </Toolbar>
            </AppBar>
            <CssBaseline />

            <Drawer variant="permanent" sx={{ width: 400, flexShrink: 0, [`& .MuiDrawer-paper`]: { width: 400, boxSizing: 'border-box' }, }}>
            <Toolbar />
            <Box sx={{ m: 1}}>

                <TextField
                    sx={{ m: 1, width: '90%' }}
                    id="keywords"
                    label="Keywords"
                    variant="standard"
                    value={searchState.keywords} // Set the value of the text field
                    onChange={(e) => setSearchState({...searchState, keywords: e.target.value})} // Update the state when the value changes
                />    
                <TextField
                    sx={{ m: 1, width: '90%' }}
                    multiline
                    id="query"
                    label="Query"
                    variant="standard"
                    value={searchState.query} // Set the value of the text field
                    onChange={(e) => setSearchState({...searchState, query: e.target.value})} // Update the state when the value changes
                />
                <Typography gutterBottom>Max results</Typography>
                <Slider sx={{ m: 1, width: '90%' }} defaultValue={searchState.max_results}
                        min={1} max={5} aria-label="Default" 
                    marks={marks}
                    valueLabelDisplay="auto" 
                    onChangeCommitted={(e,v) => setSearchState({...searchState, max_results: v as number})} />
               
                <LoadingButton
                    disabled={searchState.keywords.trim() === '' || searchState.query.trim() === ''}
                    sx={{ m: 1 }}
                    onClick={() => callApi(true)}
                    endIcon={<SendIcon />}
                    loading={searchState.loading}
                    loadingPosition="end"
                    variant="contained">from sharepoint</LoadingButton>

                <LoadingButton
                    disabled={searchState.keywords.trim() === '' || searchState.query.trim() === ''}
                    sx={{ m: 1 }}
                    onClick={() => callApi(false)}
                    endIcon={<SendIcon />}
                    loading={searchState.loading}
                    loadingPosition="end"
                    variant="contained">from preindexed</LoadingButton>            
            </Box>
            </Drawer>

        <Box component="main" sx={{ flexGrow: 1, p:3 }}>

            <ResultGrid results={searchState.results} 
                onSelected={(item) => lightboxOpened(item)} 
                onQuery={(item)=> queryResult(item)}
                onVisit={(uri)=> openInNewTab(uri)}/>

        </Box>    

        <Modal
            open={lightbox.open}
            onClose={lightboxClosed}
            aria-labelledby="modal-modal-title"
            aria-describedby="modal-modal-description" >
            <Box sx={modalStyle}>
                <img src={lightbox.image} width={'80%'} />
            </Box>
        </Modal>

        <Modal
            open={completions.open && completions.content !== ''}
            onClose={completionsResultClosed}
            aria-labelledby="modal-modal-title"
            aria-describedby="modal-modal-description" >
            <Box sx={modalStyle}>
                <Typography component="p">{completions.content}</Typography>
            </Box>
        </Modal>
        { socketUrl !== '' && <Intercom socketUrl={socketUrl} /> }
        
    </Box>);
  }

export default Main;