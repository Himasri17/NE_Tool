import React from 'react';
import {
    Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Box, List, ListItem, ListItemIcon, ListItemText, Divider
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import IconButton from '@mui/material/IconButton';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import GroupIcon from '@mui/icons-material/Group';
import SecurityIcon from '@mui/icons-material/Security';
import WarningIcon from '@mui/icons-material/Warning';
import RateReviewIcon from '@mui/icons-material/RateReview';

export default function TermsDialog({ open, onClose }) {
    const organizationName = 'NE.IIITH';

    return (
        <Dialog 
            open={open} 
            onClose={onClose} 
            aria-labelledby="terms-dialog-title"
            maxWidth="md"
            fullWidth
            scroll="paper"
        >
            <DialogTitle id="terms-dialog-title" sx={{ 
                m: 0, 
                p: 3, 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                backgroundColor: (theme) => theme.palette.primary.main, 
                color: 'white' 
            }}>
                <Typography variant="h5" component="span" sx={{ fontWeight: 'bold' }}>
                    Terms and Conditions
                </Typography>
                <IconButton
                    aria-label="close"
                    onClick={onClose}
                    sx={{ color: 'white' }}
                >
                    <CloseIcon />
                </IconButton>
            </DialogTitle>
            
            <DialogContent dividers sx={{ py: 3 }}>
                {/* Introduction */}
                <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, color: 'primary.main' }}>
                        1. Agreement to Terms
                    </Typography>
                    <Typography variant="body1" sx={{ mb: 2 }}>
                        Welcome to the NE (Named Entity) Annotation Tool provided by <strong>{organizationName}</strong>. 
                        By accessing and using this platform, you agree to be bound by these Terms and Conditions, 
                        along with our NE Annotation Guidelines and User Guidelines.
                    </Typography>
                </Box>
                
                <Divider sx={{ my: 3 }} />

                {/* User Registration & Roles */}
                <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, color: 'primary.main' }}>
                        2. User Registration & Roles
                    </Typography>
                    
                    <List dense sx={{ mb: 2 }}>
                        <ListItem sx={{ px: 0, alignItems: 'flex-start' }}>
                            <ListItemIcon sx={{ minWidth: 36, mt: 0.5 }}><GroupIcon fontSize="small" color="primary" /></ListItemIcon>
                            <ListItemText 
                                primary={
                                    <Typography variant="body2">
                                        <strong>For Admins:</strong> While registering select role as Admin and fill all other necessary credentials.
                                        Responsible for project management, user assignments, and overall system administration.
                                    </Typography>
                                }
                            />
                        </ListItem>
                        <ListItem sx={{ px: 0, alignItems: 'flex-start' }}>
                            <ListItemIcon sx={{ minWidth: 36, mt: 0.5 }}><GroupIcon fontSize="small" color="primary" /></ListItemIcon>
                            <ListItemText 
                                primary={
                                    <Typography variant="body2">
                                        <strong>For Annotators:</strong> While registering select role as Annotator and make sure you select 
                                        organisation and language as required by your admin. Responsible for creating initial annotations.
                                    </Typography>
                                }
                            />
                        </ListItem>
                        <ListItem sx={{ px: 0, alignItems: 'flex-start' }}>
                            <ListItemIcon sx={{ minWidth: 36, mt: 0.5 }}><RateReviewIcon fontSize="small" color="secondary" /></ListItemIcon>
                            <ListItemText 
                                primary={
                                    <Typography variant="body2">
                                        <strong>For Reviewers:</strong> While registering select role as Reviewer. Responsible for 
                                        validating and reviewing annotations created by annotators, ensuring quality and consistency 
                                        across the annotation projects.
                                    </Typography>
                                }
                            />
                        </ListItem>
                    </List>
                </Box>
                
                <Divider sx={{ my: 3 }} />

                {/* Project Management */}
                <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, color: 'primary.main' }}>
                        3. Project Management & File Upload
                    </Typography>
                    
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, color: 'text.primary' }}>
                        For Administrators:
                    </Typography>
                    <List dense sx={{ mb: 2 }}>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleOutlineIcon fontSize="small" color="success" /></ListItemIcon>
                            <ListItemText 
                                primary="Upload New Project: You can start by uploading your own project to begin the annotation process." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleOutlineIcon fontSize="small" color="success" /></ListItemIcon>
                            <ListItemText 
                                primary="File type can be a raw txt file and please consider to use sentence delimiters (?, !, ! , ! ! )." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleOutlineIcon fontSize="small" color="success" /></ListItemIcon>
                            <ListItemText 
                                primary="Select an Existing Project: You can also choose a project that has already been uploaded." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleOutlineIcon fontSize="small" color="success" /></ListItemIcon>
                            <ListItemText 
                                primary="Assign Reviewers: Administrators can assign reviewers to projects for quality control." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                    </List>

                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, color: 'text.primary' }}>
                        For Annotators & Reviewers:
                    </Typography>
                    <List dense>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleOutlineIcon fontSize="small" color="success" /></ListItemIcon>
                            <ListItemText 
                                primary="Select an Existing Project: You can choose a project that has already been uploaded by your admin." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                    </List>
                </Box>
                
                <Divider sx={{ my: 3 }} />

                {/* Annotation Process */}
                <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, color: 'primary.main' }}>
                        4. Annotation Process Guidelines
                    </Typography>
                    
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, color: 'text.primary' }}>
                        Steps for Annotation:
                    </Typography>
                    <List dense sx={{ mb: 2 }}>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleOutlineIcon fontSize="small" color="success" /></ListItemIcon>
                            <ListItemText 
                                primary="Viewing and Selecting Sentences: Click on any sentence from the list to start working on it." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleOutlineIcon fontSize="small" color="success" /></ListItemIcon>
                            <ListItemText 
                                primary="Select Words: Click and select words from the segmented sentence." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleOutlineIcon fontSize="small" color="success" /></ListItemIcon>
                            <ListItemText 
                                primary="Click on Annotate: After selecting the words, click on the Annotate button to proceed." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleOutlineIcon fontSize="small" color="success" /></ListItemIcon>
                            <ListItemText 
                                primary="Choosing Annotation Type: Select the NE type and its subtype from the dropdown menu." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleOutlineIcon fontSize="small" color="success" /></ListItemIcon>
                            <ListItemText 
                                primary="Add Annotation: Click Add to apply the annotation." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                    </List>

                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, color: 'text.primary' }}>
                        For Reviewers:
                    </Typography>
                    <List dense>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><RateReviewIcon fontSize="small" color="secondary" /></ListItemIcon>
                            <ListItemText 
                                primary="Review annotations created by annotators and provide feedback or corrections." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><RateReviewIcon fontSize="small" color="secondary" /></ListItemIcon>
                            <ListItemText 
                                primary="Ensure consistency and quality across all annotations in the project." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                    </List>
                </Box>

                <Divider sx={{ my: 3 }} />

                {/* Annotation Management */}
                <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, color: 'primary.main' }}>
                        5. Annotation Management
                    </Typography>
                    
                    <List dense sx={{ mb: 2 }}>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleOutlineIcon fontSize="small" color="success" /></ListItemIcon>
                            <ListItemText 
                                primary="View Annotations: See the list of annotated words on the right-hand side of the screen." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleOutlineIcon fontSize="small" color="success" /></ListItemIcon>
                            <ListItemText 
                                primary="Delete Annotations: Remove specific annotations from the list." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleOutlineIcon fontSize="small" color="success" /></ListItemIcon>
                            <ListItemText 
                                primary="Reset Annotations: Clear all annotations if needed." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleOutlineIcon fontSize="small" color="success" /></ListItemIcon>
                            <ListItemText 
                                primary="Edit Annotations: Can edit annotated words if needed." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                        <ListItem sx={{ px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleOutlineIcon fontSize="small" color="success" /></ListItemIcon>
                            <ListItemText 
                                primary="Submit Annotations: Once all annotations for a sentence are complete, click Submit to save your work." 
                                primaryTypographyProps={{ variant: 'body2' }}
                            />
                        </ListItem>
                    </List>
                </Box>
                
                <Divider sx={{ my: 3 }} />

                {/* Data Download & Intellectual Property */}
                <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, color: 'primary.main' }}>
                        6. Data Download & Intellectual Property
                    </Typography>
                    <ListItem sx={{ px: 0, alignItems: 'flex-start' }}>
                        <ListItemIcon sx={{ minWidth: 36, mt: 0.5 }}><SecurityIcon fontSize="small" color="secondary" /></ListItemIcon>
                        <ListItemText 
                            primary={
                                <Typography variant="body2" sx={{ mb: 1 }}>
                                    All annotation data created through this platform remains the intellectual 
                                    property of <strong>{organizationName}</strong>. 
                                </Typography>
                            }
                        />
                    </ListItem>
                    <Typography variant="body2" sx={{ ml: 6, mb: 1 }}>
                        To download your annotations, return to the Projects Page and click on the Download icon 
                        next to the relevant project. Download access is available for Admins, assigned Annotators, and Reviewers.
                    </Typography>
                </Box>
                
                <Divider sx={{ my: 3 }} />

                {/* Continuous Improvement & Support */}
                <Box sx={{ mb: 2 }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, color: 'primary.main' }}>
                        7. Continuous Improvement & Support
                    </Typography>
                    <ListItem sx={{ px: 0, alignItems: 'flex-start' }}>
                        <ListItemIcon sx={{ minWidth: 36, mt: 0.5 }}><WarningIcon fontSize="small" color="warning" /></ListItemIcon>
                        <ListItemText 
                            primary={
                                <Typography variant="body2">
                                    We are continuously working on improving the NE Tool based on user feedback. 
                                    The platform is provided for annotation purposes as described in the guidelines.
                                </Typography>
                            }
                        />
                    </ListItem>
                    <Typography variant="body2" sx={{ mt: 2 }}>
                        Feel free to share your suggestions for better functionality and usability. 
                        If you have any questions or need further assistance, please contact our team.
                    </Typography>
                </Box>
            </DialogContent>
            
            <DialogActions sx={{ p: 3 }}>
                <Button 
                    onClick={onClose} 
                    color="primary" 
                    variant="contained" 
                    size="large"
                    sx={{ minWidth: 120 }}
                >
                    I Understand
                </Button>
            </DialogActions>
        </Dialog>
    );
}