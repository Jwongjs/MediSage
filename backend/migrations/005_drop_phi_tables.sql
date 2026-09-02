-- MediSage is now fully anonymous: no accounts, no stored health data.
-- Retires every table that held patient information.
--
-- NOT reversible. diagnosis_sessions and medical_reports contain user health
-- data; user_profiles contains account details. Supabase's own auth.users is
-- managed by Supabase and is NOT dropped here — delete those users from the
-- Supabase dashboard if you want the accounts gone too.
drop table if exists diagnosis_sessions;
drop table if exists medical_reports;
drop table if exists user_profiles;
