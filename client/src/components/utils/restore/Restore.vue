<template>
  <div>
    <v-card>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <v-flex xs12>
            <v-form ref="form" style="padding:5px">
              <v-autocomplete v-model="server" :items="serverItems" label="Server" :rules="[v => !!v || '']"></v-autocomplete>
              <v-text-field v-model="database" label="Database" :rules="[v => !!v || '']" style="padding-top:0px" hide-details></v-text-field>
              <div class="text-subtitle-1 font-weight-regular white--text" style="margin-top:20px">SOURCE</div>
              <v-radio-group v-model="source" style="margin-top:10px; margin-bottom:15px" hide-details>
                <v-radio value="file">
                  <template v-slot:label>
                    <div>File</div>
                  </template>
                </v-radio>
                <v-radio value="url">
                  <template v-slot:label>
                    <div>URL</div>
                  </template>
                </v-radio>
                <v-radio value="s3">
                  <template v-slot:label>
                    <div>Amazon S3</div>
                  </template>
                </v-radio>
              </v-radio-group>
              <v-file-input v-show="source == 'file'" v-model="file" show-size accept=".sql" label="Click to import a .sql file" prepend-icon truncate-length="100" hide-details></v-file-input>
              <v-text-field v-show="source == 'url'" v-model="url" label="URL" :rules="[v => !!v || '']" hide-details></v-text-field>

            </v-form>
          </v-flex>
        </v-layout>
      </v-container>
    </v-card>
  </div>
</template>

<script>
export default {
  data() {
    return {
      serverItems: ['a','b','c'],
      server: '',
      database: '',
      source: 'file',
      file: null,
      url: '',
    }
  },
  created() {

  },
  methods: {

  }
}
</script>