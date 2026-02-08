import { createTheme } from '@mui/material/styles';

// SharePoint RAG Helper - Custom Theme
// A modern, professional theme with SharePoint-inspired colors

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#0078d4', // Microsoft/SharePoint blue
      light: '#2b88d8',
      dark: '#005a9e',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#6264a7', // Teams purple accent
      light: '#8b8cc7',
      dark: '#464775',
      contrastText: '#ffffff',
    },
    background: {
      default: '#faf9f8', // Fluent off-white
      paper: '#ffffff',
    },
    text: {
      primary: '#323130', // Fluent dark gray
      secondary: '#605e5c',
    },
    error: {
      main: '#d13438',
    },
    warning: {
      main: '#ffaa44',
    },
    success: {
      main: '#107c10', // Microsoft green
    },
    divider: '#edebe9',
  },
  typography: {
    fontFamily: [
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 600,
    },
    h5: {
      fontSize: '1rem',
      fontWeight: 600,
    },
    h6: {
      fontSize: '0.875rem',
      fontWeight: 600,
    },
    body1: {
      fontSize: '0.875rem',
    },
    body2: {
      fontSize: '0.75rem',
    },
    button: {
      textTransform: 'none', // Modern look - no uppercase buttons
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 4,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          padding: '8px 16px',
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.14)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 1.6px 3.6px rgba(0, 0, 0, 0.13), 0 0.3px 0.9px rgba(0, 0, 0, 0.11)',
          borderRadius: 4,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0 1.6px 3.6px rgba(0, 0, 0, 0.13), 0 0.3px 0.9px rgba(0, 0, 0, 0.11)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: '1px solid #edebe9',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            '&:hover fieldset': {
              borderColor: '#0078d4',
            },
          },
        },
      },
    },
    MuiModal: {
      styleOverrides: {
        root: {
          '& .MuiBackdrop-root': {
            backgroundColor: 'rgba(0, 0, 0, 0.4)',
          },
        },
      },
    },
  },
});

export default theme;
