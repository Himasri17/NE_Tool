import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
    Container, Box, Typography, TextField, Button, Paper, Link as MuiLink,
    InputAdornment, IconButton, FormControl, InputLabel, Select, MenuItem, useTheme,
    CircularProgress, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions,
    Chip, OutlinedInput, Checkbox, ListItemText // ADD THESE IMPORTS
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import EmailIcon from '@mui/icons-material/Email';
import LockIcon from '@mui/icons-material/Lock';
import LanguageIcon from '@mui/icons-material/Language';
import GroupIcon from '@mui/icons-material/Group';
import BusinessIcon from '@mui/icons-material/Business';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import TermsDialog from './TermsDialog';
import ContactUsDialog from '../User/ContactUsDialog';

// ADD THIS CONSTANT FOR MULTI-SELECT STYLING
const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

export default function Register() {
    // --- State Management ---
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('user');
    const [organization, setOrganization] = useState('');
    const [languages, setLanguages] = useState([]); // CHANGE TO ARRAY FOR MULTI-SELECT
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    
    // Dialog states
    const [isContactDialogOpen, setIsContactDialogOpen] = useState(false);
    const [isTermsDialogOpen, setIsTermsDialogOpen] = useState(false);
    
    // Success/Error popup states
    const [popupOpen, setPopupOpen] = useState(false);
    const [popupTitle, setPopupTitle] = useState('');
    const [popupMessage, setPopupMessage] = useState('');
    const [popupType, setPopupType] = useState('success');

    const navigate = useNavigate();
    const theme = useTheme();

    // --- Dropdown Options (UNCHANGED) ---
    const roleOptions = [{ value: 'user', label: 'Annotator/User' }, { value: 'admin', label: 'Admin' }, { value: 'reviewer', label: 'Reviewer' }, { value: 'developer', label: 'Developer' }];
    const languageOptions = ['English', 'Hindi', 'Marathi', 'Assamese', 'Boro', 'Nepali', 'Manipuri', 'Bangla', 'Maithili', 'Konkani'];
    const organizationOptions = [
        'NBU', 'DU', 'IITM', 'IITB', 'IIT BHU', 'GU', 'IIITH',
        'NIT Manipur', 'NIT Meghalaya', 'JNU', 'CDAC-Pune', 'CDAC kolkata', 'Goa University'
    ];

    // --- Show Popup Handler ---
    const showPopup = (title, message, type = 'error') => {
        setPopupTitle(title);
        setPopupMessage(message);
        setPopupType(type);
        setPopupOpen(true);
    };

    // --- Close Popup Handler ---
    const handleClosePopup = () => {
        setPopupOpen(false);
        if (popupType === 'success') {
            navigate('/login');
        }
    };

    // --- Register Handler (UPDATED FOR MULTI-SELECT LANGUAGES) ---
    const handleRegister = async (event) => {
        event.preventDefault();
        setError('');
        const isDeveloper = role.toLowerCase() === 'developer';
        const isAdmin = role.toLowerCase() === 'admin';
        
        // Validation
        if (!fullName || !email || !password || !role) {
            setError("Please fill in all required fields.");
            return;
        }
    
        // Conditional Field Check
        if (!isDeveloper && !organization) {
            setError("Organization is mandatory for non-developer roles.");
            return;
        }

        // Language validation for Admin role
        if (isAdmin && (!languages || languages.length === 0)) {
            setError("Please select at least one language for Admin role.");
            return;
        }

        setIsLoading(true);

        try {
            const response = await fetch('http://127.0.0.1:5001/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    fullName,
                    email,
                    password,
                    role, 
                    organization: isDeveloper ? "SYSTEM_DEVELOPER" : organization,
                    languages: isDeveloper ? ["N/A"] : languages, // Use the array directly for multi-select
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                const message = data.message || "Registration failed. Please try again.";
                showPopup("Registration Failed", message, 'error');
                return;
            }

            showPopup("Registration Successful", data.message, 'success');

        } catch (err) {
            console.error("Network Error during registration:", err);
            showPopup("Network Error", "Network error. Could not connect to the registration service.", 'error');
        } finally {
            setIsLoading(false);
        }
    };
    
    // --- Password Visibility Handlers (UNCHANGED) ---
    const handleClickShowPassword = () => { setShowPassword(!showPassword); };
    const handleMouseDownPassword = (event) => { event.preventDefault(); };

    // --- DIALOG HANDLERS ---
    const handleOpenContactDialog = (e) => { 
        e.preventDefault();
        setIsContactDialogOpen(true); 
    };
    const handleCloseContactDialog = () => { setIsContactDialogOpen(false); };
    const handleOpenTermsDialog = (e) => { 
        e.preventDefault();
        setIsTermsDialogOpen(true); 
    };
    const handleCloseTermsDialog = () => { setIsTermsDialogOpen(false); };

    // --- Handle Role Change (RESET LANGUAGES WHEN ROLE CHANGES) ---
    const handleRoleChange = (e) => {
        const newRole = e.target.value;
        setRole(newRole);
        
        // Reset languages when role changes to non-admin or developer
        if (newRole.toLowerCase() !== 'admin' || newRole.toLowerCase() === 'developer') {
            setLanguages([]);
        }
    };

    // --- JSX Render ---
    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', justifyContent: 'center', alignItems: 'center', backgroundColor: theme.palette.grey[100], }}>
            
            <Container component="main" maxWidth="sm" sx={{ my: 4 }}>
                <Paper elevation={6} sx={{ padding: 4, display: 'flex', flexDirection: 'column', alignItems: 'center', borderRadius: theme.shape.borderRadius * 2, borderTop: `5px solid ${theme.palette.secondary.main}`, }}>
                    <Typography component="h1" variant="h5" sx={{ mb: 1, fontWeight: 'bold' }}>Create an Account</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>Please fill in all the required information to get started.</Typography>

                    <Box component="form" onSubmit={handleRegister} noValidate sx={{ width: '100%' }}>
                        {/* Form fields remain unchanged */}
                        
                        <TextField 
                            margin="normal" 
                            required 
                            fullWidth 
                            label="Full Name" 
                            variant="outlined" 
                            value={fullName} 
                            onChange={(e) => setFullName(e.target.value)} 
                            sx={{ mb: 2 }} 
                            InputProps={{ 
                                startAdornment: (<InputAdornment position="start"><PersonIcon color="action" /></InputAdornment>), 
                            }} 
                            disabled={isLoading}
                        />
                        <TextField 
                            margin="normal" 
                            required 
                            fullWidth 
                            label="Email" 
                            type="email" 
                            variant="outlined" 
                            value={email} 
                            onChange={(e) => setEmail(e.target.value)} 
                            sx={{ mb: 2 }} 
                            InputProps={{ 
                                startAdornment: (<InputAdornment position="start"><EmailIcon color="action" /></InputAdornment>), 
                            }} 
                            disabled={isLoading}
                        />
                        <TextField
                            margin="normal" 
                            required 
                            fullWidth 
                            label="Password" 
                            type={showPassword ? 'text' : 'password'} 
                            variant="outlined" 
                            value={password} 
                            onChange={(e) => setPassword(e.target.value)} 
                            sx={{ mb: 2 }}
                            InputProps={{ 
                                startAdornment: (<InputAdornment position="start"><LockIcon color="action" /></InputAdornment>), 
                                endAdornment: (<InputAdornment position="end"><IconButton onClick={handleClickShowPassword} onMouseDown={handleMouseDownPassword} edge="end" disabled={isLoading}>{showPassword ? <VisibilityOff /> : <Visibility />}</IconButton></InputAdornment>), 
                            }}
                            disabled={isLoading}
                        />
                        
                        <FormControl 
                            fullWidth 
                            margin="normal" 
                            required={role.toLowerCase() === 'admin'} 
                            sx={{ mb: 2 }}
                        >
                            <InputLabel id="languages-label">Select Languages</InputLabel>
                            
                            {role.toLowerCase() === 'admin' ? (
                                // Multi-select with checkboxes for admin
                                <Select
                                    labelId="languages-label"
                                    multiple
                                    value={languages}
                                    onChange={(e) => setLanguages(e.target.value)}
                                    input={<OutlinedInput label="Select Languages" />}
                                    renderValue={(selected) => (
                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                            {selected.map((value) => (
                                                <Chip key={value} label={value} size="small" />
                                            ))}
                                        </Box>
                                    )}
                                    MenuProps={MenuProps}
                                    disabled={isLoading}
                                >
                                    {languageOptions.map((language) => (
                                        <MenuItem key={language} value={language}>
                                            <Checkbox checked={languages.indexOf(language) > -1} />
                                            <ListItemText primary={language} />
                                        </MenuItem>
                                    ))}
                                </Select>
                            ) : (
                                // Single-select for non-admin (except developer)
                                <Select 
                                    labelId="languages-label" 
                                    value={languages} 
                                    onChange={(e) => setLanguages(e.target.value)} 
                                    label="Select Languages"
                                    disabled={isLoading || role.toLowerCase() === 'developer'}
                                    startAdornment={<InputAdornment position="start"><LanguageIcon color="action" /></InputAdornment>}
                                >
                                    {languageOptions.map((lang) => (
                                        <MenuItem key={lang} value={lang}>
                                            {lang}
                                        </MenuItem>
                                    ))}
                                </Select>
                            )}
                            
                            {role.toLowerCase() === 'admin' && (
                                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, fontStyle: 'italic' }}>
                                    💡 You can choose multiple languages using checkboxes
                                </Typography>
                            )}
                            {role.toLowerCase() !== 'admin' && role.toLowerCase() !== 'developer' && (
                                <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                                    Select your preferred language
                                </Typography>
                            )}
                            {role.toLowerCase() === 'developer' && (
                                <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                                    Languages not required for developer role
                                </Typography>
                            )}
                        </FormControl>

                        <FormControl fullWidth margin="normal" required sx={{ mb: 2 }}>
                            <InputLabel id="role-label">Role</InputLabel>
                            <Select 
                                labelId="role-label" 
                                value={role} 
                                onChange={handleRoleChange} // Use the updated handler
                                label="Role" 
                                startAdornment={<InputAdornment position="start"><GroupIcon color="action" /></InputAdornment>}
                                disabled={isLoading}
                            >
                                {roleOptions.map((option) => (
                                    <MenuItem key={option.value} value={option.value}>
                                        {option.label}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                        
                        <FormControl fullWidth margin="normal" required={role.toLowerCase() !== 'developer'} sx={{ mb: 1 }}>
                            <InputLabel id="organization-label">Organization</InputLabel>
                            <Select 
                                labelId="organization-label" 
                                value={organization} 
                                onChange={(e) => setOrganization(e.target.value)} 
                                label="Organization" 
                                disabled={isLoading || role.toLowerCase() === 'developer'}
                                startAdornment={<InputAdornment position="start"><BusinessIcon color="action" /></InputAdornment>}
                            >
                                {organizationOptions.map((org) => (
                                    <MenuItem key={org} value={org}>{org}</MenuItem>
                                ))}
                            </Select>
                        </FormControl>

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
                            color="secondary" 
                            sx={{ mt: 3, mb: 2, py: 1.5, fontWeight: 'bold', letterSpacing: 1 }} 
                            disabled={isLoading}
                        >
                            {isLoading ? <CircularProgress size={24} color="inherit" /> : 'CREATE ACCOUNT'}
                        </Button>
                        
                        <Typography align="center" variant="body2" color="text.secondary">
                            Already have an account?{' '}
                            <MuiLink component={Link} to="/login" underline="hover">Sign In</MuiLink>
                        </Typography>
                    </Box>
                </Paper>
            </Container>

            {/* --- FOOTER --- */}
            <Box component="footer" sx={{ py: 3, px: 2, mt: 'auto', backgroundColor: theme.palette.grey[200], width: '100%', borderTop: `1px solid ${theme.palette.divider}` }}>
                <Container maxWidth="lg" sx={{ display: 'flex', justifyContent: 'center', gap: 4 }}>
                    <MuiLink component="a" href="#" onClick={handleOpenContactDialog} color="inherit" underline="hover" variant="body2">
                        Contact Us
                    </MuiLink>
                    <MuiLink component="a" href="#" onClick={handleOpenTermsDialog} color="inherit" underline="hover" variant="body2">
                        Terms & Conditions
                    </MuiLink>
                </Container>
            </Box>

            {/* --- CONTACT US DIALOG --- */}
            <ContactUsDialog 
                open={isContactDialogOpen} 
                onClose={handleCloseContactDialog} 
            /> 

            {/* --- TERMS DIALOG --- */}
            <TermsDialog 
                open={isTermsDialogOpen}
                onClose={handleCloseTermsDialog}
            />

            {/* --- SUCCESS/ERROR POPUP DIALOG --- */}
            <Dialog
                open={popupOpen}
                onClose={handleClosePopup}
                aria-labelledby="alert-dialog-title"
                aria-describedby="alert-dialog-description"
            >
                <DialogTitle 
                    id="alert-dialog-title"
                    sx={{ 
                        color: popupType === 'success' ? 'success.main' : 'error.main',
                        fontWeight: 'bold'
                    }}
                >
                    {popupTitle}
                </DialogTitle>
                <DialogContent>
                    <DialogContentText id="alert-dialog-description">
                        {popupMessage}
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button 
                        onClick={handleClosePopup} 
                        autoFocus
                        color={popupType === 'success' ? 'success' : 'error'}
                        variant="contained"
                    >
                        OK
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}