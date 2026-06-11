import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from 'contexts/AuthContext';
import { AuthService } from 'services/auth';
import { MedicalReportService, MedicalReport } from 'services/report';
import { PageLayout } from 'components/layout/PageLayout';
import { MedicalReportModal } from 'components/medical/MedicalReportModal';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { LogOut, User, Activity, ShieldCheck, Trash2, Eye, RefreshCw } from 'lucide-react';
import { UserProfile } from 'types/auth';

const ProfilePage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [userData, setUserData] = useState<UserProfile>({ name: '', email: '', age: '', gender: '' });
  const [profileLoading, setProfileLoading] = useState(false);

  const [medicalReports, setMedicalReports] = useState<MedicalReport[]>([]);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [reportsError, setReportsError] = useState<string | null>(null);
  const [selectedReport, setSelectedReport] = useState<MedicalReport | null>(null);

  const fetchUserProfile = async () => {
    setProfileLoading(true);
    try {
      const data = await AuthService.getProfile();
      setUserData({ name: data.name || '', email: data.email || '', age: data.age || '', gender: data.gender || '' });
    } finally {
      setProfileLoading(false);
    }
  };

  const fetchMedicalReports = async () => {
    setReportsLoading(true);
    setReportsError(null);
    try {
      const response = await MedicalReportService.getUserMedicalReports(20, 0);
      setMedicalReports(response.reports);
    } catch {
      setReportsError('Failed to load medical reports.');
    } finally {
      setReportsLoading(false);
    }
  };

  useEffect(() => {
    fetchUserProfile();
    fetchMedicalReports();
  }, []);

  const handleReportDelete = async (reportId: string) => {
    if (!window.confirm('Delete this report? This cannot be undone.')) return;
    try {
      await MedicalReportService.deleteMedicalReport(reportId);
      setMedicalReports(prev => prev.filter(r => r.id !== reportId));
    } catch {
      setReportsError('Failed to delete report.');
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const email    = userData.email || (user as any)?.email || '';
  const initials = email.slice(0, 2).toUpperCase() || 'ME';

  const formatDate = (d: string) =>
    new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });

  return (
    <PageLayout>
      <div className="container mx-auto max-w-3xl px-4 py-10">

        <div className="flex items-center gap-4 mb-8 flex-wrap">
          <Avatar className="h-14 w-14 shrink-0">
            <AvatarFallback className="bg-primary/10 text-primary font-semibold text-lg">{initials}</AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <h1 className="text-xl font-bold truncate">{userData.name || email || 'Your account'}</h1>
            <div className="flex items-center gap-1.5 mt-1">
              <ShieldCheck className="h-3.5 w-3.5 text-accent shrink-0" />
              <span className="text-xs text-muted-foreground">Account active</span>
            </div>
          </div>
          <Button variant="outline" size="sm" className="ml-auto gap-1.5 shrink-0" onClick={handleLogout}>
            <LogOut className="h-3.5 w-3.5" />Log out
          </Button>
        </div>

        <Tabs defaultValue="overview">
          <TabsList className="mb-6">
            <TabsTrigger value="overview" className="gap-1.5"><User className="h-3.5 w-3.5" />Overview</TabsTrigger>
            <TabsTrigger value="sessions" className="gap-1.5"><Activity className="h-3.5 w-3.5" />Sessions</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <Card className="shadow-sm">
              <CardHeader className="pb-3"><CardTitle className="text-base">Account information</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {profileLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-4 w-48" />
                  </div>
                ) : (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Email</span>
                      <span className="text-sm font-medium">{email}</span>
                    </div>
                    {userData.name && (
                      <>
                        <Separator />
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">Username</span>
                          <span className="text-sm font-medium">{userData.name}</span>
                        </div>
                      </>
                    )}
                    {userData.age && (
                      <>
                        <Separator />
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">Age group</span>
                          <span className="text-sm font-medium">{userData.age}</span>
                        </div>
                      </>
                    )}
                    <Separator />
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Privacy policy</span>
                      <Badge variant="outline" className="text-xs gap-1">
                        <ShieldCheck className="h-3 w-3 text-accent" />Accepted
                      </Badge>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
            <Card className="shadow-sm border-destructive/20">
              <CardHeader className="pb-3">
                <CardTitle className="text-base text-destructive">Danger zone</CardTitle>
                <CardDescription>Irreversible account actions.</CardDescription>
              </CardHeader>
              <CardContent>
                <Button variant="destructive" size="sm" onClick={handleLogout}>Sign out of all sessions</Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sessions">
            <Card className="shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between pb-3">
                <div>
                  <CardTitle className="text-base">Diagnostic sessions</CardTitle>
                  <CardDescription>Your saved MediSage medical reports.</CardDescription>
                </div>
                <Button variant="ghost" size="sm" onClick={fetchMedicalReports} disabled={reportsLoading} className="gap-1.5">
                  <RefreshCw className={`h-3.5 w-3.5 ${reportsLoading ? 'animate-spin' : ''}`} />Refresh
                </Button>
              </CardHeader>
              <CardContent>
                {reportsError && (
                  <Alert variant="destructive" className="mb-4">
                    <AlertDescription>{reportsError}</AlertDescription>
                  </Alert>
                )}
                {reportsLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3].map(i => <Skeleton key={i} className="h-16 w-full" />)}
                  </div>
                ) : medicalReports.length === 0 ? (
                  <div className="text-center py-10 space-y-2">
                    <Activity className="h-8 w-8 text-muted-foreground/30 mx-auto" />
                    <p className="text-sm text-muted-foreground">No reports yet.</p>
                    <Button size="sm" variant="outline" onClick={() => navigate('/diagnosis')}>
                      Start a diagnosis
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {medicalReports.map(report => (
                      <div key={report.id} className="flex items-start justify-between gap-3 p-3 rounded-lg border bg-secondary/30 hover:bg-secondary/50 transition-colors">
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium truncate">{report.report_title}</p>
                          {report.overall_analysis?.final_diagnosis && (
                            <p className="text-xs text-muted-foreground truncate">{report.overall_analysis.final_diagnosis}</p>
                          )}
                          <p className="text-xs text-muted-foreground mt-0.5">{formatDate(report.created_at)}</p>
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          <Button size="icon" variant="ghost" className="h-7 w-7" onClick={() => setSelectedReport(report)}>
                            <Eye className="h-3.5 w-3.5" />
                          </Button>
                          <Button size="icon" variant="ghost" className="h-7 w-7 text-destructive hover:text-destructive" onClick={() => handleReportDelete(report.id)}>
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

      </div>

      {selectedReport && (
        <MedicalReportModal
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
        />
      )}
    </PageLayout>
  );
};

export default ProfilePage;
