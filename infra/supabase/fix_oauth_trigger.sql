-- FIX: Update the handle_new_user trigger to properly handle OAuth users
-- Run this in Supabase SQL Editor

-- Drop the existing trigger first
drop trigger if exists on_auth_user_created on auth.users;

-- Create an improved function that handles OAuth users
create or replace function public.handle_new_user()
returns trigger as $$
declare
  user_full_name text;
  user_role_value text;
  user_role_enum user_role;
begin
  -- Get full name from metadata, or extract from email
  user_full_name := coalesce(
    new.raw_user_meta_data->>'full_name',
    new.raw_user_meta_data->>'name',  -- Google OAuth uses 'name' not 'full_name'
    split_part(new.email, '@', 1)
  );
  
  -- Get role from metadata, default to NULL (pending approval)
  user_role_value := new.raw_user_meta_data->>'role';
  
  -- Only set role if it's a valid enum value, otherwise leave it NULL (no role = pending)
  if user_role_value in ('ADMIN', 'DOCTOR', 'ASHA_WORKER') then
    user_role_enum := user_role_value::user_role;
  else
    -- For OAuth users without a role, we'll skip inserting (but Supabase Auth still creates the user)
    -- They'll need admin approval to get a role assigned
    user_role_enum := null;
  end if;

  -- Insert into user_profiles (allow NULL role for pending users)
  insert into public.user_profiles (id, email, full_name, role, is_active)
  values (
    new.id,
    new.email,
    user_full_name,
    user_role_enum,
    true
  )
  on conflict (id) do update set
    email = excluded.email,
    full_name = excluded.full_name,
    updated_at = now();
    
  return new;
exception when others then
  -- Log the error but don't fail the user creation
  raise warning 'Failed to create user_profile for %: %', new.email, sqlerrm;
  return new;
end;
$$ language plpgsql security definer;

-- Recreate the trigger
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- Also need to update the user_profiles table to allow NULL role (for pending approval)
alter table public.user_profiles 
  alter column role drop not null;

-- Add a policy to allow the trigger to insert (bypass RLS)
-- The security definer should handle this, but just in case:
create policy "Service role can insert profiles"
  on public.user_profiles for insert
  with check (true);

-- IMPORTANT: Also check if there's RLS blocking service role
-- You may need to run this:
-- grant all on public.user_profiles to service_role;

select 'Trigger updated successfully! OAuth users will now be created with NULL role (pending approval).' as status;
