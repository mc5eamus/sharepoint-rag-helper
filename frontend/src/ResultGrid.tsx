import React, { useState, useEffect} from "react";


import Card from '@mui/material/Card';
import Box from '@mui/material/Box';
import Grid from "@mui/material/Grid";
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import QuestionMark from '@mui/icons-material/QuestionMark';
import Forward from '@mui/icons-material/Forward';
import CardMedia from "@mui/material/CardMedia";
import CardActions from "@mui/material/CardActions";
import Button from "@mui/material/Button";

interface ResultGridProps {
    results: any[];
    onSelected: (item:any) => void;
    onQuery: (item:any) => void;
    onVisit: (url:any) => void;
}

const ResultGrid:React.FC<ResultGridProps> = ({results, onSelected, onQuery, onVisit}) => {

    const [state, setState] = useState({ items: results});

    useEffect(() => {
        setState({ items: results});
    }, [results]);

    return (
            <Grid container spacing={4}>
                { state.items.map((result: any) => {
                    return <Grid item xs={4} key={result.id} >
                        <Card variant="outlined" sx={{ display: 'flex' }}>
                        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <CardContent>
                            <Typography sx={{ fontSize: 10 }} noWrap style={{textOverflow: 'ellipsis'}}  color="text.secondary" gutterBottom>
                                <a href={result.uri}>{result.title}</a>
                            </Typography>
                            <Typography  maxHeight={100} style={{overflow:"hidden"}} sx={{ fontSize: 10 }} 
                                component="div">
                                {result.content}
                            </Typography>
                        </CardContent>
                        <CardActions>
                            <Button size="small" variant="contained" startIcon={<QuestionMark/>} onClick={() => onQuery(result)}>Query</Button>
                            <Button size="small" variant="contained" startIcon={<Forward/>} onClick={() => onVisit(result.uri)}>Visit</Button>
                        </CardActions>
                        </Box>
                        { result.snapshot && 
                <CardMedia
                    component="img"
                    style={{ cursor: 'pointer' }}
                    onClick={() => onSelected(result)}
                    sx={{ width: 200, height: 200 }}
                    image={"http://localhost:8085/api/media/" + result.snapshot}/>
                }
                </Card></Grid>})

        }</Grid> );
  }

export default ResultGrid;