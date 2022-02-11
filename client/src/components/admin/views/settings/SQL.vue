<template>
  <v-flex xs12 style="margin:5px">
    <div class="text-h6 font-weight-regular"><v-icon small style="margin-right:10px; margin-bottom:3px; color:#fa8131">fas fa-database</v-icon>SQL</div>
    <div class="body-1 font-weight-regular" style="margin-top:10px">The SQL credentials where Meteor Next is stored.</div>
    <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.hostname" label="Hostname" style="margin-top:15px;" required :rules="[v => !!v || '']"></v-text-field>
    <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.port" label="Port" style="padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
    <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.username" label="Username" style="padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
    <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.password" label="Password" style="padding-top:0px;" @click:append="show_password = !show_password" :append-icon="show_password ? 'visibility' : 'visibility_off'" :type="show_password ? 'text' : 'password'" required :rules="[v => !!v || '']"></v-text-field>
    <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.database" label="Database" style="padding-top:0px; margin-bottom:5px" required :rules="[v => !!v || '']" hide-details></v-text-field>
    <v-card v-if="sql.ssl_client_key != null || sql.ssl_client_certificate != null || sql.ssl_ca_certificate != null" style="height:52px; margin-top:15px">
      <v-row no-gutters>
      <v-col cols="auto" style="display:flex; margin:15px">
        <v-icon color="#00b16a" style="font-size:17px; margin-top:2px">fas fa-key</v-icon>
      </v-col>
      <v-col>
        <div class="text-body-1" style="color:#00b16a; margin-top:15px">{{ 'Using a SSL connection (' + ssl_active + ')' }}</div>
      </v-col>
      </v-row>
    </v-card>
  </v-flex>
</template>

<script>
export default {
  data: () => ({
    sql: {},
    show_password: false,
    loading: false,
  }),
  props: ['info','init'],
  created() {
    if (Object.keys(this.info).length > 0) this.sql = JSON.parse(JSON.stringify(this.info))
  },
  watch: {
    info: function(val) {
      this.sql = JSON.parse(JSON.stringify(val))
    },
    init: function(val) {
      this.loading = val
    }
  },
  computed: {
    ssl_active: function() {
      let elements = []
      if (this.sql.ssl_client_key != null) elements.push('Client Key')
      if (this.sql.ssl_client_certificate != null) elements.push('Client Certificate')
      if (this.sql.ssl_ca_certificate != null) elements.push('CA Certificate')
      return elements.join(' + ')
    }
  },
}
</script>