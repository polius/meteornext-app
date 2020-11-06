<template>
  <div>
    <!------------------------->
    <!-- BOTTOMBAR - SERVERS -->
    <!------------------------->
    <div style="height:35px; border-top:2px solid #2c2c2c;">
      <v-btn text small title="Refresh Connections" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
      <v-btn text small title="New Connection" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
      <v-btn text small title="Remove Connection" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn text small title="New Folder" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-folder</v-icon></v-btn>
    </div>
  </div>
</template>

<script>

export default {
  data() {
    return {
    }
  },
}
</script>