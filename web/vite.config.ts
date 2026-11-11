import { defineConfig, loadEnv } from 'vite';
export default defineConfig(({mode})=>{const target=loadEnv(mode,'.','').FLUIDLAB_API_URL||'http://127.0.0.1:8000';return {server:{port:5173,strictPort:true,proxy:{'/api':target,'/health':target}},test:{environment:'jsdom'}} as any});
