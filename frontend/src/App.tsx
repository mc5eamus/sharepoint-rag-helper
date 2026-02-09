import './App.css';
import Main from './Main';
import { MsalProvider, AuthenticatedTemplate, UnauthenticatedTemplate, useMsal } from "@azure/msal-react";
import { IPublicClientApplication } from "@azure/msal-browser";
import { loginRequest } from "./config";

import { ThemeProvider, CssBaseline } from '@mui/material';
import Button from '@mui/material/Button';
import LoginIcon from '@mui/icons-material/Login';
import theme from './theme';

type AppProps = {
  pca: IPublicClientApplication;
};

function LoginComponent () {
  const { instance } = useMsal();

  const handleLogin = () => {
      instance.loginRedirect(loginRequest).catch((error) => {
          console.error("Login failed:", error);
      });
  }

  return <Button variant='contained' endIcon={<LoginIcon />} onClick={handleLogin}>sign in</Button>;
};

function App({ pca }: AppProps) {

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <MsalProvider instance={pca}>
        <div className="App">
          <header className="App-header">
            <AuthenticatedTemplate>
              <Main/>
            </AuthenticatedTemplate>
            <UnauthenticatedTemplate>
              <LoginComponent/>
            </UnauthenticatedTemplate>
          </header>
        </div>
      </MsalProvider>
    </ThemeProvider>
  );
}

export default App;
