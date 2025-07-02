

namespace VoterRegistryApi.Dtos
{
    public class PagedResult<T>
    {
        public int ResultCount { get; set; }

        public int Offset { get; set; }

        public int TotalCount { get; set; }

        public List<T> Results { get; set; } = new List<T>();

        public PagedResult(int resultCount, int offset, int totalCount, List<T> results)
        {
            ResultCount = resultCount;
            Offset = offset;
            TotalCount = totalCount;
            Results = results ?? new List<T>();
        }
    }
}