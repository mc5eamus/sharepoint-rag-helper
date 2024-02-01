import './App.css';
import Main from './Main';
import { MsalProvider, AuthenticatedTemplate, UnauthenticatedTemplate, useMsal } from "@azure/msal-react";
import { IPublicClientApplication } from "@azure/msal-browser";
import { loginRequest } from "./config";
import { useEffect } from "react";

import Button from '@mui/material/Button';
import LoginIcon from '@mui/icons-material/Login';

type AppProps = {
  pca: IPublicClientApplication;
};

function LoginComponent () {
  const { instance, inProgress } = useMsal();

  useEffect(() => {
  }, [inProgress, instance]);

  const handleLogin = (loginType: string) => {
      if (loginType === "popup") {
          instance.loginPopup(loginRequest);
      } else if (loginType === "redirect") {
          instance.loginRedirect(loginRequest);
      }
  }

  return <Button variant='contained' endIcon={<LoginIcon />} onClick={() => handleLogin("popup")}>sign in</Button>;
};

function App({ pca }: AppProps) {

  return (
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
  );
}

export default App;
