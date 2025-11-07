import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
    Container, Box, Typography, TextField, Button, Paper, Link as MuiLink,
    InputAdornment, IconButton, useTheme, Grid, CircularProgress
} from '@mui/material';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import PersonIcon from '@mui/icons-material/Person';
import LockIcon from '@mui/icons-material/Lock';
import TermsDialog from './TermsDialog';
import SupportDialog from './SupportDialog';

export default function Login() {
    const [username, setLoginUsername] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [termsDialogOpen, setTermsDialogOpen] = useState(false);
    const [supportDialogOpen, setSupportDialogOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false); 
    const navigate = useNavigate();
    const theme = useTheme();

    const handleLogin = async (event) => {
        event.preventDefault();
        setError('');
        
        if (!username.trim() || !password.trim()) {
            setError('Please fill in all required fields');
            return;
        }
        
        setIsLoading(true);

        try {
            const response = await fetch('http://127.0.0.1:5001/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json();
            
            if (!response.ok) {
                const message = data.error || data.message || "Login failed. Please try again.";
                
                if (message.includes("awaiting approval")) {
                    setError(`Your account is pending approval by a ${data.role === 'admin' ? 'developer' : 'Admin'}. You will be notified by email when activated.`);
                } else if (message.includes("rejected")) {
                    setError(`Your account registration was rejected. Reason: ${data.rejection_reason || 'Contact support.'}`);
                } else {
                    setError(message);
                }
                return;
            }

            // In Login.js - Replace the storage section after successful login
            if (data.token && data.username && data.role) {
                // Store token separately
                localStorage.setItem('jwt_token', data.token);
                
                // Store user data as a JSON object under 'user' key (this is what RoleRouter expects)
                const userData = {
                    username: data.username,
                    role: data.role,
                    token: data.token
                };
                localStorage.setItem('user', JSON.stringify(userData));
                
                // Also store individual fields for backward compatibility
                localStorage.setItem('username', data.username);
                localStorage.setItem('userRole', data.role);
                
                console.log(`[Login Success] Stored user data and token for role: ${data.role}`);
                
                // Navigate to /home - RoleRouter will handle the redirection
                navigate('/home'); 

            } else {
                console.error('[Login] ERROR: API response missing critical fields');
                setError("Login response missing key data. Please contact support.");
                return;
            }

            navigate('/home'); 

        } catch (err) {
            setError('Network error. Please ensure the backend is running at http://127.0.0.1:5001.');
            console.error('Network error:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleClickShowPassword = () => { setShowPassword(!showPassword); };
    const handleMouseDownPassword = (event) => { event.preventDefault(); };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', justifyContent: 'center', alignItems: 'center', backgroundColor: theme.palette.grey[100], }}>
            <Container component="main" maxWidth="sm" sx={{ mb: 4 }}>
                <Typography variant="h4" align="center" color="text.primary" gutterBottom sx={{ mb: 4, fontWeight: 600, letterSpacing: 1.5, color: theme.palette.primary.main }}>
                    Annotation Platform Access
                </Typography>

                <Paper elevation={6} sx={{ padding: 4, display: 'flex', flexDirection: 'column', alignItems: 'center', borderRadius: theme.shape.borderRadius * 2, borderTop: `5px solid ${theme.palette.primary.main}`, }}>
                    <Typography component="h1" variant="h5" sx={{ mb: 1, fontWeight: 'bold' }}>Sign In</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>Enter your credentials to access your account</Typography>

                    <Box component="form" onSubmit={handleLogin} noValidate sx={{ width: '100%' }}>
                        <TextField 
                            fullWidth 
                            margin="normal" 
                            required 
                            id="username" 
                            label="Username (Email)" 
                            name="username" 
                            autoFocus 
                            variant="outlined" 
                            value={username} 
                            onChange={(e) => setLoginUsername(e.target.value)}
                            sx={{ mb: 2 }} 
                            InputProps={{ 
                                startAdornment: (<InputAdornment position="start"><PersonIcon color="action" /></InputAdornment>), 
                            }} 
                            disabled={isLoading}
                        />
                        <TextField 
                            fullWidth 
                            margin="normal" 
                            required 
                            name="password" 
                            label="Password" 
                            type={showPassword ? 'text' : 'password'} 
                            id="password" 
                            variant="outlined" 
                            value={password} 
                            onChange={(e) => setPassword(e.target.value)} 
                            sx={{ mb: 1 }}
                            InputProps={{
                                startAdornment: (<InputAdornment position="start"><LockIcon color="action" /></InputAdornment>),
                                endAdornment: (<InputAdornment position="end"><IconButton aria-label="toggle password visibility" onClick={handleClickShowPassword} onMouseDown={handleMouseDownPassword} edge="end" disabled={isLoading}>{showPassword ? <VisibilityOff /> : <Visibility />}</IconButton></InputAdornment>),
                            }}
                            disabled={isLoading}
                        />
                        
                        {/* Forgot Password Link */}
                        <Box sx={{ textAlign: 'right', mb: 2 }}>
                            <MuiLink 
                                component={Link} 
                                to="/forgot-password" 
                                variant="body2" 
                                underline="hover"
                            >
                                Forgot your password?
                            </MuiLink>
                        </Box>
                        
                        {error && (
                            <Typography color="error" variant="body2" sx={{ mt: 1, mb: 2 }}>
                                {error}
                            </Typography>
                        )}

                        <Button 
                            type="submit" 
                            fullWidth 
                            variant="contained" 
                            size="large" 
                            sx={{ mt: 1, mb: 2, py: 1.5, fontWeight: 'bold', letterSpacing: 1 }}
                            disabled={isLoading}
                        >
                            {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Sign In'}
                        </Button>
                        
                        <Typography align="center" variant="body2" color="text.secondary">
                            Don't have an account?{' '}<MuiLink component={Link} to="/register" underline="hover">Sign Up</MuiLink>
                        </Typography>
                    </Box>
                </Paper>
            </Container>

            {/* Footer */}
            <Box component="footer" sx={{ py: 3, px: 2, mt: 'auto', backgroundColor: theme.palette.grey[200], width: '100%', borderTop: `1px solid ${theme.palette.divider}` }}>
                <Container maxWidth="lg">
                    <Grid container justifyContent="space-around" alignItems="center">
                        <Grid item>
                            <MuiLink 
                                color="inherit" 
                                component="button" 
                                type="button"
                                onClick={() => setSupportDialogOpen(true)}
                                sx={{ border: 'none', background: 'none', cursor: 'pointer', font: 'inherit' }}
                            >
                                Support
                            </MuiLink>
                        </Grid>
                        <Grid item>
                            <MuiLink 
                                color="inherit" 
                                component="button" 
                                type="button"
                                onClick={() => setTermsDialogOpen(true)}
                                sx={{ border: 'none', background: 'none', cursor: 'pointer', font: 'inherit' }}
                            >
                                Terms
                            </MuiLink>
                        </Grid>
                    </Grid>
                    <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
                        {'© 2025 Annotation Platform. All rights reserved.'}
                    </Typography>
                </Container>
            </Box>

            {/* Terms Dialog */}
            <TermsDialog 
                open={termsDialogOpen}
                onClose={() => setTermsDialogOpen(false)}
            />

            {/* Support Dialog */}
            <SupportDialog 
                open={supportDialogOpen}
                onClose={() => setSupportDialogOpen(false)}
            />
        </Box>
    );
}
