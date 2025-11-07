import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
    Container, Box, Typography, Card, CardContent, Grid, CircularProgress, Alert, Button, Chip,
    List, ListItem, Divider, useTheme,
    Dialog, DialogTitle, DialogContent, TextField,
} from '@mui/material';

import RateReviewIcon from '@mui/icons-material/RateReview';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import VisibilityIcon from '@mui/icons-material/Visibility';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import { getAuthHeaders, removeToken} from '../../components/authUtils'; 

// UPDATE THESE IMPORT STATEMENTS
import ContactUsDialog from '../User/ContactUsDialog';
import FeedbackDialog from '../User/FeedbackDialog';
import TermsDialog from '../User Authentication/TermsDialog'; // ADD THIS IMPORT

const API_BASE_URL = 'http://127.0.0.1:5001';

// Helper function to get the reviewer's username (email)
const getReviewerUsername = () => { 
    return localStorage.getItem('username') || 'reviewer@example.com';
} 


const fetchReviewerStats = async (username) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/analytics/reviewer-stats`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch reviewer statistics');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching reviewer stats:', error);
        return { totalProjects: 0, totalSentencesReviewed: 0, pendingReviews: 0, reviewAccuracy: 0 };
    }
};

// NEW: Fetches the live queue of PENDING_REVIEW sentences
const fetchPendingSentencesAPI = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/reviewer/pending_sentences`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch pending sentences queue');
        return await response.json();
    } catch (error) {
        console.error('Error fetching pending sentences:', error);
        return [];
    }
};

const ReviewDialog = ({ open, onClose, sentence, reviewerUsername, fetchDashboardData, theme }) => {
    const handleTagApprove = async (tagId, reviewer) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/reviewer/tag/${tagId}/approve`, {
                method: 'PUT',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    reviewer_username: reviewer
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to approve tag');
            }

            // Success: Refresh the data and close dialog
            await fetchDashboardData();
            alert('Tag approved successfully!');
            onClose(); // ADD THIS LINE TO CLOSE THE DIALOG
            
        } catch (err) {
            console.error('Error during tag approval:', err);
            alert(`Tag Approval Failed: ${err.message}`);
        }
    };

    const handleTagReject = async (tagId, comment, reviewer) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/reviewer/tag/${tagId}/reject`, {
                method: 'PUT',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    reviewer_username: reviewer,
                    comments: comment
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to reject tag');
            }

            // Success: Refresh the data and close dialog
            await fetchDashboardData();
            alert('Tag rejected successfully!');
            onClose(); // ADD THIS LINE TO CLOSE THE DIALOG
            
        } catch (err) {
            console.error('Error during tag rejection:', err);
            alert(`Tag Rejection Failed: ${err.message}`);
        }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <Box sx={{ bgcolor: '#f0f0f0', p: 2, borderTopLeftRadius: 4, borderTopRightRadius: 4 }}>
                <DialogTitle sx={{ p: 0, fontWeight: 'bold' }}>Review Annotation</DialogTitle>
            </Box>
            <DialogContent sx={{ p: 3 }}>
                {/* Sentence Text */}
                <Typography variant="body1" sx={{ mb: 2, fontWeight: 'bold' }}>
                    Sentence: <span style={{ fontWeight: 'normal', fontStyle: 'italic' }}>{sentence?.sentence_text || 'Loading...'}</span>
                </Typography>

                {/* Individual Tags with Approve/Reject Buttons */}
                {sentence?.tags && sentence.tags.length > 0 && (
                    <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 2 }}>
                            Individual Tag Review ({sentence.tags.length} tags):
                        </Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            {sentence.tags.map((tag, index) => (
                                <Card 
                                    key={tag._id || index} 
                                    variant="outlined" 
                                    sx={{ 
                                        p: 2,
                                        borderLeft: `4px solid ${
                                            tag.review_status === 'Approved' ? '#4CAF50' : 
                                            tag.review_status === 'Rejected' ? '#F44336' : 
                                            '#FF9800'
                                        }`
                                    }}
                                >
                                    <Grid container spacing={2} alignItems="center">
                                        <Grid item xs={12} sm={6}>
                                            <Typography variant="body2" fontWeight="bold">
                                                Phrase: <span style={{ fontWeight: 'normal' }}>"{tag.text}"</span>
                                            </Typography>
                                            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                                                <Typography variant="body2" fontWeight="bold" sx={{ mr: 1 }}>
                                                    Type:
                                                </Typography>
                                                <Chip 
                                                    label={tag.tag} 
                                                    size="small" 
                                                    sx={{ 
                                                        bgcolor: '#1976d2',
                                                        color: 'white',
                                                        fontWeight: 'bold'
                                                    }}
                                                />
                                            </Box>
                                            <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 1 }}>
                                                Annotator: {tag.username}
                                            </Typography>
                                            <Typography variant="caption" display="block" color="text.secondary">
                                                Status: 
                                                <Chip 
                                                    label={tag.review_status || 'Pending'} 
                                                    size="small"
                                                    sx={{ 
                                                        ml: 1,
                                                        bgcolor: 
                                                            tag.review_status === 'Approved' ? '#4CAF50' : 
                                                            tag.review_status === 'Rejected' ? '#F44336' : 
                                                            '#FF9800',
                                                        color: 'white',
                                                        fontSize: '0.7rem'
                                                    }}
                                                />
                                            </Typography>
                                        </Grid>
                                        <Grid item xs={12} sm={6}>
                                            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                                                {tag.review_status !== 'Approved' && (
                                                    <Button 
                                                        variant="contained" 
                                                        size="small"
                                                        color="success" 
                                                        onClick={() => handleTagApprove(tag._id, reviewerUsername)}
                                                        sx={{ bgcolor: '#4CAF50' }} 
                                                        startIcon={<CheckCircleIcon />}
                                                    >
                                                        Approve Tag
                                                    </Button>
                                                )}
                                                {tag.review_status !== 'Rejected' && (
                                                    <Button 
                                                        variant="contained" 
                                                        size="small"
                                                        color="error" 
                                                        onClick={() => {
                                                            const comment = prompt("Please enter rejection reason for this tag:");
                                                            if (comment !== null) {
                                                                handleTagReject(tag._id, comment, reviewerUsername);
                                                            }
                                                        }}
                                                        sx={{ bgcolor: '#F44336' }} 
                                                        startIcon={<CancelIcon />}
                                                    >
                                                        Reject Tag
                                                    </Button>
                                                )}
                                            </Box>
                                        </Grid>
                                    </Grid>
                                </Card>
                            ))}
                        </Box>
                    </Box>
                )}

                {/* Info message about individual tag review */}
                <Box sx={{ mt: 3, p: 2, bgcolor: '#e3f2fd', borderRadius: 1 }}>
                    <Typography variant="body2" color="primary" align="center">
                        Review each tag individually. The sentence will automatically move out of the queue when all tags are reviewed.
                    </Typography>
                </Box>
            </DialogContent>
        </Dialog>
    );
};

const ViewDetailsDialog = ({ open, onClose, details }) => {
    const theme = useTheme();

    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>Annotation Details</DialogTitle>
            <DialogContent>
                {/* Sentence Text */}
                <Box sx={{ mb: 3, p: 2, border: '1px solid #e0e0e0', borderRadius: 2, bgcolor: '#fafafa' }}>
                    <Typography variant="subtitle1" fontWeight="bold" sx={{ mb: 1 }}>Sentence:</Typography>
                    <Typography variant="body1" sx={{ fontStyle: 'italic', lineHeight: 1.5 }}>
                        {details?.sentence_text || 'N/A'}
                    </Typography>
                </Box>

                {/* Tags Section */}
                <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" fontWeight="bold" sx={{ mb: 2 }}>
                        Identified Tags ({details?.tags?.length || 0})
                    </Typography>
                    
                    {details?.tags && details.tags.length > 0 ? (
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            {details.tags.map((tag, index) => (
                                <Card 
                                    key={tag._id || index} 
                                    variant="outlined" 
                                    sx={{ 
                                        p: 2, 
                                        borderLeft: `4px solid ${
                                            tag.review_status === 'Approved' ? '#4CAF50' : 
                                            tag.review_status === 'Rejected' ? '#F44336' : 
                                            '#FF9800'
                                        }`
                                    }}
                                >
                                    <Grid container spacing={1} alignItems="center">
                                        <Grid item xs={12} sm={6}>
                                            <Typography variant="body2" fontWeight="bold">
                                                Phrase: <span style={{ fontWeight: 'normal' }}>"{tag.text}"</span>
                                            </Typography>
                                            <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                                                <Typography variant="body2" fontWeight="bold" sx={{ mr: 1 }}>
                                                    Type:
                                                </Typography>
                                                <Chip 
                                                    label={tag.tag} 
                                                    size="small" 
                                                    sx={{ 
                                                        bgcolor: theme.palette.primary.main, 
                                                        color: 'white',
                                                        fontWeight: 'bold'
                                                    }}
                                                />
                                            </Box>
                                        </Grid>
                                        <Grid item xs={12} sm={6}>
                                            <Typography variant="caption" display="block" color="text.secondary">
                                                Annotator: {tag.username}
                                            </Typography>
                                            <Typography variant="caption" display="block" color="text.secondary">
                                                Status: 
                                                <Chip 
                                                    label={tag.review_status || 'Pending'} 
                                                    size="small"
                                                    sx={{ 
                                                        ml: 1,
                                                        bgcolor: 
                                                            tag.review_status === 'Approved' ? '#4CAF50' : 
                                                            tag.review_status === 'Rejected' ? '#F44336' : 
                                                            '#FF9800',
                                                        color: 'white',
                                                        fontSize: '0.7rem'
                                                    }}
                                                />
                                            </Typography>
                                            {tag.annotation_date && (
                                                <Typography variant="caption" display="block" color="text.secondary">
                                                    Date: {new Date(tag.annotation_date).toLocaleDateString()}
                                                </Typography>
                                            )}
                                        </Grid>
                                    </Grid>
                                </Card>
                            ))}
                        </Box>
                    ) : (
                        <Alert severity="info">
                            No tags identified for this sentence.
                        </Alert>
                    )}
                </Box>

                {/* Debug Information */}
                <Card variant="outlined" sx={{ bgcolor: theme.palette.grey[100], p: 2 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, color: theme.palette.primary.dark, fontWeight: 'bold' }}>
                        Sentence Information
                    </Typography>
                    <Typography variant="caption" component="div" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                        {`Sentence ID: ${details?.id || 'N/A'}\nAnnotator: ${details?.annotatorUsername || 'N/A'}\nProject: ${details?.project_name || 'N/A'}\nProject ID: ${details?.projectId || 'N/A'}\nReview Status: ${details?.review_status || 'Pending'}`}
                    </Typography>
                </Card>
            </DialogContent>
        </Dialog>
    );
};


// ----------------------------------------------------------------------
// --- REVIEWER DASHBOARD MAIN COMPONENT ---
// ----------------------------------------------------------------------

export default function ReviewerDashboard() {
    const navigate = useNavigate();
    const { username } = useParams();
    const reviewerUsername = getReviewerUsername();
    const theme = useTheme(); 
    
    // --- State ---
    const [reviewerStats, setReviewerStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [pendingSentences, setPendingSentences] = useState([]); // Live queue data
    
    // Dialog States
    const [isReviewDialogOpen, setIsReviewDialogOpen] = useState(false);
    const [isViewDetailsDialogOpen, setIsViewDetailsDialogOpen] = useState(false);
    const [currentReviewItem, setCurrentReviewItem] = useState(null);
    const [openFeedbackDialog, setOpenFeedbackDialog] = useState(false);
    
    // UPDATE THESE STATE VARIABLES FOR FOOTER DIALOGS
    const [isContactUsOpen, setIsContactUsOpen] = useState(false);
    const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
    const [isTermsOpen, setIsTermsOpen] = useState(false); // ADD THIS STATE

    // --- Data Fetching Logic (UPDATED) ---
    const fetchDashboardData = useCallback(async () => {
        setLoading(true);
        
        try {
            // 1. Fetch live pending sentences
            const sentences = await fetchPendingSentencesAPI();
            setPendingSentences(sentences);
            
            // 2. Fetch overall stats
            const backendStats = await fetchReviewerStats(reviewerUsername);

            const realStats = {
                // Update pending count based on the live queue size
                pendingReviews: sentences.length, 
                totalProjects: backendStats.totalProjects || 0,
                totalSentencesReviewed: backendStats.totalSentencesReviewed || 0,
                reviewAccuracy: backendStats.reviewAccuracy || 0
            };
            
            setReviewerStats(realStats);

        } catch (err) {
            console.error("Reviewer Dashboard Error:", err);
        } finally {
            setLoading(false);
        }
    }, [reviewerUsername]);

    useEffect(() => {
        fetchDashboardData();
        // Set up polling to update the list every 30 seconds
        const interval = setInterval(fetchDashboardData, 30000);
        return () => clearInterval(interval);
    }, [fetchDashboardData]); 
    
  
    
    const handleReviewClick = (sentence) => {
        setCurrentReviewItem(sentence);
        setIsReviewDialogOpen(true);
    };

    const handleViewClick = (sentence) => {
        setCurrentReviewItem(sentence);
        setIsViewDetailsDialogOpen(true);
    };
    
    const handleLogout = async () => {
        removeToken();
        localStorage.removeItem('username');
        navigate("/login");
    };

    // UPDATE THESE HANDLERS FOR FOOTER BUTTONS
    const handleContactUs = () => {
        setIsContactUsOpen(true);
    };

    const handleFeedback = () => {
        setIsFeedbackOpen(true);
    };

    const handleOpenFeedbackDialog = () => setOpenFeedbackDialog(true);
    const handleCloseFeedbackDialog = () => setOpenFeedbackDialog(false);

    const handleTerms = () => {
        setIsTermsOpen(true); // UPDATE THIS TO OPEN TERMS DIALOG
    };

    // --- Component Rendering ---
    
    if (loading && !reviewerStats) {
        return (
            <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
                 <Box sx={{ 
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '60px', 
                    bgcolor: theme.palette.primary.main, color: 'white', p: 2, width: '100%', boxSizing: 'border-box'
                }}>
                    <Typography variant="h6" fontWeight={500}>MWE Expression Workbench</Typography>
                    <CircularProgress size={20} color="inherit" />
                </Box>
                <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    <CircularProgress />
                </Box>
            </Box>
        );
    }
    
    return (
        <Box sx={{ 
            minHeight: '100vh', 
            width: '100vw', 
            margin: 0, 
            padding: 0, 
            bgcolor: theme.palette.grey[200],
            display: 'flex',
            flexDirection: 'column'
        }}>
            
            {/* TOP NAVIGATION BAR */}
            <Box sx={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                height: '60px', 
                bgcolor: theme.palette.primary.main, 
                color: 'white', 
                p: 2, 
                width: '100%', 
                boxSizing: 'border-box',
                flexShrink: 0
            }}>
                <Typography variant="h6" fontWeight={500}>MWE Expression Workbench</Typography>
                <Button 
                    variant="outlined" 
                    size="small" 
                    sx={{ color: 'white', borderColor: 'white' }} 
                    onClick={handleLogout}
                >
                    LOGOUT
                </Button>
            </Box>
            {/* END TOP NAVIGATION BAR */}

            <Container component="main" maxWidth="xl" sx={{ mt: 4, mb: 4, flexGrow: 1 }}>
                
                <Typography variant="h4" component="h1" fontWeight="bold" sx={{ mb: 4 }}>
                    Reviewer Dashboard
                </Typography>

                {/* --- STATS CARD SECTION (Matching Figma Layout) --- */}
                {reviewerStats && (
                    <Card elevation={2} sx={{ mb: 4, bgcolor: theme.palette.grey[50], borderLeft: `5px solid ${theme.palette.primary.main}` }}>
                        <CardContent>
                            <Grid container spacing={3} alignItems="center">
                                {/* Total Projects */}
                                <Grid item xs={12} sm={3}>
                                    <Typography variant="subtitle2" color="text.secondary">Total Projects</Typography>
                                    <Typography variant="h5" fontWeight="bold" color="primary">{reviewerStats.totalProjects}</Typography>
                                </Grid>
                                <Divider orientation="vertical" flexItem sx={{ display: { xs: 'none', sm: 'block' } }} />

                                {/* Total Reviewed */}
                                <Grid item xs={12} sm={3}>
                                    <Typography variant="subtitle2" color="text.secondary">Total Sentences Reviewed</Typography>
                                    <Typography variant="h5" fontWeight="bold" color="success.main">{reviewerStats.totalSentencesReviewed}</Typography>
                                </Grid>
                                <Divider orientation="vertical" flexItem sx={{ display: { xs: 'none', sm: 'block' } }} />

                                {/* Pending Reviews */}
                                <Grid item xs={12} sm={3}>
                                    <Typography variant="subtitle2" color="text.secondary">Pending Review Assignments</Typography>
                                    <Typography variant="h5" fontWeight="bold" color="warning.main">{reviewerStats.pendingReviews}</Typography>
                                </Grid>
                                <Divider orientation="vertical" flexItem sx={{ display: { xs: 'none', sm: 'block' } }} />

                                {/* Review Accuracy */}
                                <Grid item xs={12} sm={3}>
                                    <Typography variant="subtitle2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center' }}>
                                        <TrendingUpIcon fontSize="small" sx={{ mr: 0.5 }} /> Review Accuracy
                                    </Typography>
                                    <Typography variant="h5" fontWeight="bold" color="primary.dark">{reviewerStats.reviewAccuracy}%</Typography>
                                </Grid>
                            </Grid>
                        </CardContent>
                    </Card>
                )}
                
                {/* --- PENDING REVIEWEES SECTION (LIVE QUEUE) --- */}
                <Box sx={{ mt: 5 }}>
                    <Typography variant="h5" fontWeight="bold" color="text.primary" sx={{ mb: 2 }}>
                        Pending Reviewees
                    </Typography>
                    
                    <Card elevation={2} sx={{ borderRadius: 2 }}>
                        <List disablePadding>
                            {pendingSentences.length > 0 ? (
                                pendingSentences.map((sentence, index) => (
                                    <React.Fragment key={sentence.id}>
                                        <ListItem sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', py: 1.5 }}>
                                            {/* Sentence Text and User/Project Info */}
                                            <Box sx={{ flexGrow: 1, minWidth: '50%' }}>
                                                <Typography variant="body1" sx={{ fontWeight: 500, mb: 1 }}>
                                                    {sentence.sentence_text}
                                                </Typography>
                                                
                                                {/* Tag Count Badge */}
                                                {sentence.tags && sentence.tags.length > 0 && (
                                                    <Chip 
                                                        label={`${sentence.tags.length} tag(s)`}
                                                        size="small"
                                                        color="primary"
                                                        variant="outlined"
                                                        sx={{ mb: 1 }}
                                                    />
                                                )}
                                                
                                                <Typography variant="caption" color="text.secondary">
                                                    Annotator: <strong>{sentence.annotatorUsername}</strong> | Project: {sentence.project_name}
                                                </Typography>
                                            </Box>

                                            {/* Action Buttons (View and Review) */}
                                            <Box sx={{ display: 'flex', gap: 1 }}>
                                                {/* VIEW Button */}
                                                <Button 
                                                    variant="outlined" 
                                                    size="small"
                                                    onClick={() => handleViewClick(sentence)}
                                                    startIcon={<VisibilityIcon />}
                                                >
                                                    View Details
                                                </Button>
                                                {/* REVIEW Button */}
                                                <Button 
                                                    variant="contained" 
                                                    size="small"
                                                    color="primary"
                                                    onClick={() => handleReviewClick(sentence)}
                                                    startIcon={<RateReviewIcon />}
                                                >
                                                    Review
                                                </Button>
                                            </Box>
                                        </ListItem>
                                        {index < pendingSentences.length - 1 && <Divider />}
                                    </React.Fragment>
                                ))
                            ) : (
                                <ListItem>
                                    <Alert severity="success" sx={{ width: '100%' }}>
                                        The review queue is currently empty. Waiting for annotators to submit sentences.
                                    </Alert>
                                </ListItem>
                            )}
                        </List>
                    </Card>
                </Box>
            </Container>

            {/* FOOTER - Now properly positioned at the bottom */}
            <Box sx={{ 
                mt: 'auto', // This pushes the footer to the bottom
                textAlign: 'center', 
                color: 'text.secondary', 
                borderTop: '1px solid #ccc', 
                pt: 2,
                pb: 2,
                width: '100%',
                flexShrink: 0
            }}>
                <Button size="small" sx={{ mr: 2 }} onClick={handleContactUs}>CONTACT US</Button>
                <Button size="small" sx={{ mr: 2 }} onClick={handleOpenFeedbackDialog}>FEEDBACK</Button>
                <Button size="small" onClick={handleTerms}>TERMS</Button>
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    © 2025 MWE Annotation Platform. All rights reserved.
                </Typography>
            </Box>

            {currentReviewItem && (
                <ReviewDialog
                    open={isReviewDialogOpen}
                    onClose={() => setIsReviewDialogOpen(false)}
                    sentence={currentReviewItem}
                    reviewerUsername={reviewerUsername}
                    fetchDashboardData={fetchDashboardData}
                    theme={theme}
                />
            )}
            
            {currentReviewItem && (
                <ViewDetailsDialog
                    open={isViewDetailsDialogOpen}
                    onClose={() => setIsViewDetailsDialogOpen(false)}
                    details={currentReviewItem}
                />
            )}

            {/* UPDATE FOOTER DIALOGS */}
            <ContactUsDialog
                open={isContactUsOpen}
                onClose={() => setIsContactUsOpen(false)}
            />
            
            <FeedbackDialog
                open={openFeedbackDialog}
                onClose={handleCloseFeedbackDialog}
                userEmail={username} 
            />
            
            <TermsDialog
                open={isTermsOpen}
                onClose={() => setIsTermsOpen(false)}
            />
        </Box>
    );
}